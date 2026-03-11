extends Node

signal health_checked(success: bool, payload: Dictionary)
signal game_created(success: bool, payload: Dictionary)
signal snapshot_received(success: bool, payload: Dictionary)
signal grand_tichu_submitted(success: bool, payload: Dictionary)
signal exchange_submitted(success: bool, payload: Dictionary)
signal small_tichu_submitted(success: bool, payload: Dictionary)
signal play_submitted(success: bool, payload: Dictionary)
signal pass_submitted(success: bool, payload: Dictionary)
signal dragon_recipient_submitted(success: bool, payload: Dictionary)
signal legal_plays_received(success: bool, game_id: String, viewer: int, payload: Dictionary)
signal play_preview_received(success: bool, game_id: String, viewer: int, request_id: int, payload: Dictionary)
signal socket_snapshot_received(game_id: String, viewer: int, snapshot: Dictionary)
signal socket_connection_changed(connected: bool, message: String)

const BASE_URL := "http://127.0.0.1:8000"

var socket_peer: WebSocketPeer = null
var socket_game_id := ""
var socket_viewer := -1
var socket_state := WebSocketPeer.STATE_CLOSED


func _ready() -> void:
	set_process(true)


func _process(_delta: float) -> void:
	if socket_peer == null:
		return

	var poll_error := socket_peer.poll()
	if poll_error != OK:
		_clear_socket_state()
		socket_connection_changed.emit(false, "Live: socket poll failed")
		return

	var ready_state := socket_peer.get_ready_state()
	if ready_state != socket_state:
		socket_state = ready_state
		match ready_state:
			WebSocketPeer.STATE_CONNECTING:
				socket_connection_changed.emit(false, "Live: connecting...")
			WebSocketPeer.STATE_OPEN:
				socket_connection_changed.emit(true, "Live: connected")
			WebSocketPeer.STATE_CLOSING:
				socket_connection_changed.emit(false, "Live: closing...")
			WebSocketPeer.STATE_CLOSED:
				_clear_socket_state()
				socket_connection_changed.emit(false, "Live: disconnected")
				return

	if ready_state != WebSocketPeer.STATE_OPEN:
		return

	while socket_peer.get_available_packet_count() > 0:
		var text := socket_peer.get_packet().get_string_from_utf8()
		var parsed = JSON.parse_string(text)
		if typeof(parsed) != TYPE_DICTIONARY:
			continue

		var payload: Dictionary = parsed
		if str(payload.get("type", "")) != "snapshot":
			continue

		var snapshot = payload.get("snapshot", {})
		if typeof(snapshot) != TYPE_DICTIONARY:
			continue
		socket_snapshot_received.emit(
			str(payload.get("game_id", socket_game_id)),
			int(payload.get("viewer", socket_viewer)),
			snapshot
		)


func check_health() -> void:
	var payload := await _request_json("/health", HTTPClient.METHOD_GET)
	health_checked.emit(not payload.has("error"), payload)


func create_game() -> void:
	var payload := await _request_json("/games/tichu", HTTPClient.METHOD_POST)
	game_created.emit(not payload.has("error"), payload)


func get_snapshot(game_id: String, viewer: int) -> void:
	var payload := await _request_json("/games/%s?viewer=%d" % [game_id, viewer], HTTPClient.METHOD_GET)
	snapshot_received.emit(not payload.has("error"), payload)


func connect_game_socket(game_id: String, viewer: int) -> void:
	disconnect_game_socket(false)

	socket_peer = WebSocketPeer.new()
	socket_game_id = game_id
	socket_viewer = viewer
	socket_state = WebSocketPeer.STATE_CONNECTING

	var socket_url := "%s/ws/games/%s?viewer=%d" % [_websocket_base_url(), game_id, viewer]
	var connect_error := socket_peer.connect_to_url(socket_url)
	if connect_error != OK:
		_clear_socket_state()
		socket_connection_changed.emit(false, "Live: connect failed")
		return

	socket_connection_changed.emit(false, "Live: connecting...")


func disconnect_game_socket(notify: bool = true) -> void:
	if socket_peer != null:
		var ready_state := socket_peer.get_ready_state()
		if ready_state == WebSocketPeer.STATE_OPEN or ready_state == WebSocketPeer.STATE_CONNECTING:
			socket_peer.close()

	_clear_socket_state()
	if notify:
		socket_connection_changed.emit(false, "Live: disconnected")


func is_socket_connected() -> bool:
	return socket_peer != null and socket_peer.get_ready_state() == WebSocketPeer.STATE_OPEN


func is_socket_connected_for(game_id: String, viewer: int) -> bool:
	return is_socket_connected() and socket_game_id == game_id and socket_viewer == viewer


func get_legal_plays(game_id: String, viewer: int) -> void:
	var payload := await _request_json("/games/%s/legal-plays?viewer=%d" % [game_id, viewer], HTTPClient.METHOD_GET)
	legal_plays_received.emit(not payload.has("error"), game_id, viewer, payload)


func preview_play(game_id: String, viewer: int, cards: Array, call_rank: Variant, request_id: int) -> void:
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
		body
	)
	play_preview_received.emit(not payload.has("error"), game_id, viewer, request_id, payload)


func submit_grand_tichu(game_id: String, player_index: int, declare: bool) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
			"declare": declare,
		}
	)
	var payload := await _request_json(
		"/games/%s/prepare/grand-tichu" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	grand_tichu_submitted.emit(not payload.has("error"), payload)


func submit_exchange(game_id: String, player_index: int, to_left: Dictionary, to_team: Dictionary, to_right: Dictionary) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
			"to_left": to_left,
			"to_team": to_team,
			"to_right": to_right,
		}
	)
	var payload := await _request_json(
		"/games/%s/prepare/exchange" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	exchange_submitted.emit(not payload.has("error"), payload)


func submit_small_tichu(game_id: String, player_index: int) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
		}
	)
	var payload := await _request_json(
		"/games/%s/actions/small-tichu" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	small_tichu_submitted.emit(not payload.has("error"), payload)


func submit_play(game_id: String, player_index: int, cards: Array, call_rank: Variant) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
			"cards": cards,
			"call_rank": call_rank,
		}
	)
	var payload := await _request_json(
		"/games/%s/actions/play" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	play_submitted.emit(not payload.has("error"), payload)


func submit_pass(game_id: String, player_index: int) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
		}
	)
	var payload := await _request_json(
		"/games/%s/actions/pass" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	pass_submitted.emit(not payload.has("error"), payload)


func submit_dragon_recipient(game_id: String, player_index: int, recipient_index: int) -> void:
	var body := JSON.stringify(
		{
			"player_index": player_index,
			"recipient_index": recipient_index,
		}
	)
	var payload := await _request_json(
		"/games/%s/actions/dragon-recipient" % game_id,
		HTTPClient.METHOD_POST,
		body
	)
	dragon_recipient_submitted.emit(not payload.has("error"), payload)


func _request_json(path: String, method: HTTPClient.Method, body: String = "") -> Dictionary:
	var request := HTTPRequest.new()
	add_child(request)

	var headers := PackedStringArray(["Content-Type: application/json"])
	var error := request.request(BASE_URL + path, headers, method, body)
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


func _clear_socket_state() -> void:
	socket_peer = null
	socket_game_id = ""
	socket_viewer = -1
	socket_state = WebSocketPeer.STATE_CLOSED


func _websocket_base_url() -> String:
	var socket_base := BASE_URL.replace("http://", "ws://")
	socket_base = socket_base.replace("https://", "wss://")
	return socket_base
