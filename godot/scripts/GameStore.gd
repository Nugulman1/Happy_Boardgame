extends Node

var room_code := ""
var room_status := ""
var seat_token := ""
var room_snapshot: Dictionary = {}
var my_seat_index := -1
var game_id := ""
var viewer := -1
var phase := ""
var state: Dictionary = {}
var available_actions: Dictionary = {}
var round_result: Dictionary = {}
var effects: Array = []
var legal_plays: Array = []
var play_preview: Dictionary = {}
var selected_viewer := 0
var selected_actor := 0


func apply_snapshot(snapshot: Dictionary) -> void:
	game_id = str(snapshot.get("game_id", ""))
	viewer = int(snapshot.get("viewer", -1))
	selected_viewer = viewer
	selected_actor = viewer
	phase = str(snapshot.get("phase", ""))
	state = snapshot.get("state", {})
	available_actions = snapshot.get("available_actions", {})
	round_result = snapshot.get("round_result", {})
	effects = snapshot.get("effects", [])
	legal_plays.clear()
	play_preview.clear()


func apply_room_snapshot(snapshot: Dictionary) -> void:
	room_snapshot = snapshot.duplicate(true)
	room_code = str(snapshot.get("room_code", room_code))
	room_status = str(snapshot.get("status", ""))
	my_seat_index = int(snapshot.get("my_seat_index", -1))
	if my_seat_index >= 0:
		selected_viewer = my_seat_index
		selected_actor = my_seat_index
	game_id = str(snapshot.get("game_id", game_id))


func set_multiplayer_identity(next_room_code: String, seat_index: int, next_seat_token: String) -> void:
	room_code = next_room_code
	my_seat_index = seat_index
	seat_token = next_seat_token
	selected_viewer = seat_index
	selected_actor = seat_index


func clear_multiplayer_identity() -> void:
	room_code = ""
	room_status = ""
	seat_token = ""
	room_snapshot.clear()
	my_seat_index = -1
	game_id = ""
	viewer = -1
	phase = ""
	state.clear()
	available_actions.clear()
	round_result.clear()
	effects.clear()
	legal_plays.clear()
	play_preview.clear()


func has_active_game() -> bool:
	return game_id != "" and viewer >= 0


func has_active_room() -> bool:
	return room_code != "" and my_seat_index >= 0 and not seat_token.is_empty()


func set_selected_viewer(next_viewer: int) -> void:
	selected_viewer = clamp(next_viewer, 0, 3)


func set_selected_actor(next_actor: int) -> void:
	selected_actor = clamp(next_actor, 0, 3)


func set_legal_plays(next_legal_plays: Array) -> void:
	legal_plays = next_legal_plays.duplicate(true)


func clear_legal_plays() -> void:
	legal_plays.clear()


func set_play_preview(next_preview: Dictionary) -> void:
	play_preview = next_preview.duplicate(true)


func clear_play_preview() -> void:
	play_preview.clear()
