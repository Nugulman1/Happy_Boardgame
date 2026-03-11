extends Node

signal health_checked(success: bool, payload: Dictionary)
signal game_created(success: bool, payload: Dictionary)
signal snapshot_received(success: bool, payload: Dictionary)
signal room_created(success: bool, payload: Dictionary)
signal room_joined(success: bool, payload: Dictionary)
signal room_snapshot_loaded(success: bool, payload: Dictionary)
signal room_started(success: bool, payload: Dictionary)
signal room_left(success: bool, payload: Dictionary)
signal legal_plays_received(success: bool, game_id: String, viewer: int, payload: Dictionary)
signal play_preview_received(success: bool, game_id: String, viewer: int, request_id: int, payload: Dictionary)
signal socket_snapshot_received(game_id: String, viewer: int, snapshot: Dictionary)
signal room_socket_snapshot_received(room_code: String, snapshot: Dictionary)
signal socket_action_result(request_id: int, action: String, effects: Array)
signal socket_action_error(request_id: int, action: String, error_payload: Dictionary)
signal room_socket_error(message: String)
signal socket_connection_changed(connected: bool, message: String)

const BASE_URL := "http://127.0.0.1:8000"
const RECONNECT_DELAYS := [0.5, 1.0, 2.0, 4.0, 5.0]

var socket_peer: WebSocketPeer = null
var socket_state := WebSocketPeer.STATE_CLOSED
var socket_kind := ""
var socket_room_code := ""
var socket_game_id := ""
var socket_viewer := -1
var socket_seat_token := ""
var socket_request_id := 0

var desired_socket_kind := ""
var desired_room_code := ""
var desired_game_id := ""
var desired_viewer := -1
var desired_seat_token := ""
var reconnect_attempt := 0
var reconnect_wait := -1.0


func _ready() -> void:
	set_process(true)


func _process(delta: float) -> void:
	if socket_peer != null:
		socket_peer.poll()

		var ready_state := socket_peer.get_ready_state()
		if ready_state != socket_state:
			socket_state = ready_state
			match ready_state:
				WebSocketPeer.STATE_CONNECTING:
					socket_connection_changed.emit(false, "Live: connecting...")
				WebSocketPeer.STATE_OPEN:
					reconnect_attempt = 0
					reconnect_wait = -1.0
					socket_connection_changed.emit(true, "Live: connected")
				WebSocketPeer.STATE_CLOSING:
					socket_connection_changed.emit(false, "Live: closing...")
				WebSocketPeer.STATE_CLOSED:
					_handle_socket_closed("Live: disconnected")
					return

		if ready_state != WebSocketPeer.STATE_OPEN:
			return

		while socket_peer.get_available_packet_count() > 0:
			var text := socket_peer.get_packet().get_string_from_utf8()
			var parsed = JSON.parse_string(text)
			if typeof(parsed) != TYPE_DICTIONARY:
				continue
			_handle_socket_payload(parsed)
		return

	if _has_desired_socket() and reconnect_wait >= 0.0:
		reconnect_wait -= delta
		if reconnect_wait <= 0.0:
			_open_desired_socket()


func check_health() -> void:
	var payload := await _request_json("/health", HTTPClient.METHOD_GET)
	health_checked.emit(not payload.has("error"), payload)


func create_game() -> void:
	var payload := await _request_json("/games/tichu", HTTPClient.METHOD_POST)
	game_created.emit(not payload.has("error"), payload)


func get_snapshot(game_id: String, viewer: int, seat_token: String = "") -> void:
	var payload := await _request_json(
		"/games/%s" % game_id,
		HTTPClient.METHOD_GET,
		"",
		{
			"viewer": viewer,
			"seat_token": seat_token,
		}
	)
	snapshot_received.emit(not payload.has("error"), payload)


func create_room() -> void:
	var payload := await _request_json("/rooms/tichu", HTTPClient.METHOD_POST)
	room_created.emit(not payload.has("error"), payload)


func join_room(room_code: String, seat_index: int) -> void:
	var body := JSON.stringify({"seat_index": seat_index})
	var payload := await _request_json("/rooms/%s/join" % room_code, HTTPClient.METHOD_POST, body)
	room_joined.emit(not payload.has("error"), payload)


func get_room_state(room_code: String, seat_token: String) -> void:
	var payload := await _request_json(
		"/rooms/%s" % room_code,
		HTTPClient.METHOD_GET,
		"",
		{"seat_token": seat_token}
	)
	room_snapshot_loaded.emit(not payload.has("error"), payload)


func start_room(room_code: String, seat_token: String) -> void:
	var payload := await _request_json(
		"/rooms/%s/start" % room_code,
		HTTPClient.METHOD_POST,
		"",
		{"seat_token": seat_token}
	)
	room_started.emit(not payload.has("error"), payload)


func leave_room(room_code: String, seat_token: String) -> void:
	var payload := await _request_json(
		"/rooms/%s/leave" % room_code,
		HTTPClient.METHOD_POST,
		"",
		{"seat_token": seat_token}
	)
	room_left.emit(not payload.has("error"), payload)


func connect_room_socket(room_code: String, seat_token: String) -> void:
	_set_desired_socket("room", room_code, "", -1, seat_token)
	_open_desired_socket()


func connect_game_socket(game_id: String, viewer: int, seat_token: String = "") -> void:
	_set_desired_socket("game", "", game_id, viewer, seat_token)
	_open_desired_socket()


func disconnect_socket(notify: bool = true) -> void:
	_clear_desired_socket()
	if socket_peer != null:
		var ready_state := socket_peer.get_ready_state()
		if ready_state == WebSocketPeer.STATE_OPEN or ready_state == WebSocketPeer.STATE_CONNECTING:
			socket_peer.close()
	_clear_socket_state()
	if notify:
		socket_connection_changed.emit(false, "Live: disconnected")


func disconnect_game_socket(notify: bool = true) -> void:
	disconnect_socket(notify)


func disconnect_room_socket(notify: bool = true) -> void:
	disconnect_socket(notify)


func is_socket_connected() -> bool:
	return socket_peer != null and socket_peer.get_ready_state() == WebSocketPeer.STATE_OPEN


func is_socket_connected_for(game_id: String, viewer: int) -> bool:
	return (
		is_socket_connected()
		and socket_kind == "game"
		and socket_game_id == game_id
		and socket_viewer == viewer
	)


func is_room_socket_connected_for(room_code: String) -> bool:
	return is_socket_connected() and socket_kind == "room" and socket_room_code == room_code


func send_action(action: String, payload: Dictionary) -> int:
	socket_request_id += 1
	var request_id := socket_request_id
	if not is_socket_connected() or socket_kind != "game":
		socket_action_error.emit(
			request_id,
			action,
			{"code": "SOCKET_NOT_CONNECTED", "message": "live game socket is not connected"}
		)
		return request_id

	var message := JSON.stringify(
		{
			"type": "action",
			"request_id": request_id,
			"action": action,
			"payload": payload,
		}
	)
	var send_error := socket_peer.send_text(message)
	if send_error != OK:
		socket_action_error.emit(
			request_id,
			action,
			{"code": "SOCKET_SEND_FAILED", "message": error_string(send_error)}
		)
	return request_id


func get_legal_plays(game_id: String, viewer: int, seat_token: String = "") -> void:
	var payload := await _request_json(
		"/games/%s/legal-plays" % game_id,
		HTTPClient.METHOD_GET,
		"",
		{
			"viewer": viewer,
			"seat_token": seat_token,
		}
	)
	legal_plays_received.emit(not payload.has("error"), game_id, viewer, payload)


func preview_play(game_id: String, viewer: int, cards: Array, call_rank: Variant, request_id: int, seat_token: String = "") -> void:
	var body := JSON.stringify(
		{
			"viewer": viewer,
			"cards": cards,
			"call_rank": call_rank,
		}
	)
	var payload := await _request_json(
		"/games/%s/play-preview" % game_id,
		HTTPClient.METHOD_POST,
		body,
		{"seat_token": seat_token}
	)
	play_preview_received.emit(not payload.has("error"), game_id, viewer, request_id, payload)


func _handle_socket_payload(parsed: Variant) -> void:
	var payload: Dictionary = parsed
	var payload_type := str(payload.get("type", ""))
	match payload_type:
		"snapshot":
			var snapshot = payload.get("snapshot", {})
			if typeof(snapshot) != TYPE_DICTIONARY:
				return
			socket_snapshot_received.emit(
				str(payload.get("game_id", socket_game_id)),
				int(payload.get("viewer", socket_viewer)),
				snapshot
			)
		"room_snapshot":
			var snapshot = payload.get("room_snapshot", {})
			if typeof(snapshot) != TYPE_DICTIONARY:
				return
			room_socket_snapshot_received.emit(
				str(payload.get("room_code", socket_room_code)),
				snapshot
			)
		"action_result":
			var effects_payload = payload.get("effects", [])
			if typeof(effects_payload) != TYPE_ARRAY:
				effects_payload = []
			socket_action_result.emit(
				int(payload.get("request_id", -1)),
				str(payload.get("action", "")),
				effects_payload
			)
		"action_error":
			var error_payload = payload.get("error", {})
			if typeof(error_payload) != TYPE_DICTIONARY:
				error_payload = {"code": "INVALID_RESPONSE", "message": "action error payload was invalid"}
			socket_action_error.emit(
				int(payload.get("request_id", -1)),
				str(payload.get("action", "")),
				error_payload
			)
		"room_error":
			var message := str(payload.get("message", "room socket error"))
			room_socket_error.emit(message)
		_:
			return


func _set_desired_socket(kind: String, room_code: String, game_id: String, viewer: int, seat_token: String) -> void:
	desired_socket_kind = kind
	desired_room_code = room_code
	desired_game_id = game_id
	desired_viewer = viewer
	desired_seat_token = seat_token
	reconnect_attempt = 0
	reconnect_wait = 0.0


func _clear_desired_socket() -> void:
	desired_socket_kind = ""
	desired_room_code = ""
	desired_game_id = ""
	desired_viewer = -1
	desired_seat_token = ""
	reconnect_attempt = 0
	reconnect_wait = -1.0


func _has_desired_socket() -> bool:
	return not desired_socket_kind.is_empty()


func _open_desired_socket() -> void:
	if not _has_desired_socket():
		return

	if socket_peer != null:
		var ready_state := socket_peer.get_ready_state()
		if ready_state == WebSocketPeer.STATE_OPEN or ready_state == WebSocketPeer.STATE_CONNECTING:
			socket_peer.close()
	_clear_socket_state()

	socket_peer = WebSocketPeer.new()
	socket_kind = desired_socket_kind
	socket_room_code = desired_room_code
	socket_game_id = desired_game_id
	socket_viewer = desired_viewer
	socket_seat_token = desired_seat_token
	socket_state = WebSocketPeer.STATE_CONNECTING

	var socket_url := ""
	if socket_kind == "room":
		socket_url = "%s/ws/rooms/%s?seat_token=%s" % [
			_websocket_base_url(),
			socket_room_code,
			socket_seat_token.uri_encode(),
		]
	else:
		socket_url = "%s/ws/games/%s?viewer=%d" % [
			_websocket_base_url(),
			socket_game_id,
			socket_viewer,
		]
		if not socket_seat_token.is_empty():
			socket_url += "&seat_token=%s" % socket_seat_token.uri_encode()

	var connect_error := socket_peer.connect_to_url(socket_url)
	if connect_error != OK:
		_schedule_reconnect("Live: connect failed")
		return

	socket_connection_changed.emit(false, "Live: connecting...")


func _schedule_reconnect(message: String) -> void:
	_clear_socket_state()
	if not _has_desired_socket():
		socket_connection_changed.emit(false, message)
		return
	var delay_index := mini(reconnect_attempt, RECONNECT_DELAYS.size() - 1)
	reconnect_wait = RECONNECT_DELAYS[delay_index]
	reconnect_attempt += 1
	socket_connection_changed.emit(false, "%s | reconnecting in %.1fs" % [message, reconnect_wait])


func _handle_socket_closed(message: String) -> void:
	_schedule_reconnect(message)


func _request_json(path: String, method: HTTPClient.Method, body: String = "", query: Dictionary = {}) -> Dictionary:
	var request := HTTPRequest.new()
	add_child(request)

	var headers := PackedStringArray(["Content-Type: application/json"])
	var request_path := _append_query(path, query)
	var error := request.request(BASE_URL + request_path, headers, method, body)
	if error != OK:
		request.queue_free()
		return {"error": {"code": "REQUEST_FAILED", "message": error_string(error)}}

	var response: Array = await request.request_completed
	request.queue_free()

	var response_code: int = response[1]
	var raw_body: PackedByteArray = response[3]
	var text := raw_body.get_string_from_utf8()
	if text.is_empty():
		return {}

	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {"error": {"code": "INVALID_RESPONSE", "message": "response was not a JSON object"}}

	var payload: Dictionary = parsed
	if response_code < 200 or response_code >= 300:
		if not payload.has("error"):
			payload["error"] = {
				"code": "HTTP_%d" % response_code,
				"message": "request failed with status %d" % response_code,
			}
	return payload


func _append_query(path: String, query: Dictionary) -> String:
	if query.is_empty():
		return path
	var parts: Array[String] = []
	for key in query.keys():
		var value = query.get(key)
		if value == null:
			continue
		var text := str(value)
		if text.is_empty():
			continue
		parts.append("%s=%s" % [str(key).uri_encode(), text.uri_encode()])
	if parts.is_empty():
		return path
	var separator := "&" if path.contains("?") else "?"
	return "%s%s%s" % [path, separator, "&".join(parts)]


func _clear_socket_state() -> void:
	socket_peer = null
	socket_kind = ""
	socket_room_code = ""
	socket_game_id = ""
	socket_viewer = -1
	socket_seat_token = ""
	socket_state = WebSocketPeer.STATE_CLOSED


func _websocket_base_url() -> String:
	var socket_base := BASE_URL.replace("http://", "ws://")
	socket_base = socket_base.replace("https://", "wss://")
	return socket_base
