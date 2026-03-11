extends Node

var game_id := ""
var viewer := -1
var phase := ""
var state: Dictionary = {}
var available_actions: Dictionary = {}
var round_result: Dictionary = {}
var effects: Array = []
var selected_viewer := 0
var selected_actor := 0


func apply_snapshot(snapshot: Dictionary) -> void:
	game_id = str(snapshot.get("game_id", ""))
	viewer = int(snapshot.get("viewer", -1))
	phase = str(snapshot.get("phase", ""))
	state = snapshot.get("state", {})
	available_actions = snapshot.get("available_actions", {})
	round_result = snapshot.get("round_result", {})
	effects = snapshot.get("effects", [])


func has_active_game() -> bool:
	return game_id != "" and viewer >= 0


func set_selected_viewer(next_viewer: int) -> void:
	selected_viewer = clamp(next_viewer, 0, 3)


func set_selected_actor(next_actor: int) -> void:
	selected_actor = clamp(next_actor, 0, 3)
