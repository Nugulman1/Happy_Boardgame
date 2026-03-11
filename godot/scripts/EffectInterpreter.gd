extends Node

const EFFECT_TO_EVENT := {
	"game_created": "announce_game_created",
	"initial_cards_dealt": "deal_initial_cards",
	"grand_tichu_declared": "announce_grand_tichu",
	"remaining_cards_dealt": "deal_remaining_cards",
	"cards_exchanged": "complete_exchange",
	"phase_changed": "update_phase_presentation",
	"small_tichu_declared": "announce_small_tichu",
	"cards_played": "play_cards_to_table",
	"player_passed": "announce_pass",
	"dragon_recipient_required": "prompt_dragon_recipient",
	"dragon_recipient_chosen": "announce_dragon_recipient",
	"turn_changed": "highlight_current_turn",
	"trick_won": "collect_trick_cards",
	"round_finished": "announce_round_finished",
	"game_finished": "announce_game_finished",
}


func interpret_effects(effects: Array, snapshot: Dictionary) -> Array:
	var events: Array = []
	var snapshot_phase := str(snapshot.get("phase", ""))
	var snapshot_context := _snapshot_context(snapshot)

	for effect in effects:
		if typeof(effect) != TYPE_DICTIONARY:
			continue

		var effect_payload: Dictionary = effect.duplicate(true)
		var effect_type := str(effect_payload.get("type", ""))
		var event_name := str(EFFECT_TO_EVENT.get(effect_type, "unknown_effect"))
		events.append(
			{
				"name": event_name,
				"source_effect_type": effect_type,
				"snapshot_phase": snapshot_phase,
				"payload": effect_payload,
				"requires_visual_change": event_name == "highlight_current_turn",
				"snapshot_context": snapshot_context.duplicate(true),
			}
		)

	return events


func _snapshot_context(snapshot: Dictionary) -> Dictionary:
	var state: Dictionary = snapshot.get("state", {})
	var table_state: Dictionary = state.get("table", {})
	var game_state: Dictionary = state.get("game", {})

	return {
		"game_id": str(snapshot.get("game_id", "")),
		"viewer": int(snapshot.get("viewer", -1)),
		"phase": str(snapshot.get("phase", "")),
		"team_scores": game_state.get("team_scores", []),
		"round_index": game_state.get("round_index", null),
		"current_player_index": table_state.get("current_player_index", null),
		"leader_index": table_state.get("leader_index", null),
		"trick_index": table_state.get("trick_index", null),
	}
