extends Control

const ApiClientScript = preload("res://scripts/ApiClient.gd")
const GameStoreScript = preload("res://scripts/GameStore.gd")

@onready var status_label: Label = $"RootLayout/StatusLabel"
@onready var phase_label: Label = $"RootLayout/PhaseLabel"
@onready var turn_label: Label = $"RootLayout/TurnLabel"
@onready var game_info_label: Label = $"RootLayout/GameInfoLabel"
@onready var error_label: Label = $"RootLayout/ErrorLabel"
@onready var viewer_select: OptionButton = $"RootLayout/ControlRow/ViewerSelect"
@onready var actor_select: OptionButton = $"RootLayout/ControlRow/ActorSelect"
@onready var create_game_button: Button = $"RootLayout/ButtonRow/CreateGameButton"
@onready var refresh_button: Button = $"RootLayout/ButtonRow/RefreshButton"
@onready var pass_button: Button = $"RootLayout/ButtonRow/PassButton"
@onready var play_button: Button = $"RootLayout/ButtonRow/PlayButton"
@onready var small_tichu_button: Button = $"RootLayout/ButtonRow/SmallTichuButton"
@onready var grand_tichu_yes_button: Button = $"RootLayout/PrepareRow/GrandTichuYesButton"
@onready var grand_tichu_no_button: Button = $"RootLayout/PrepareRow/GrandTichuNoButton"
@onready var selected_left_label: Label = $"RootLayout/ExchangeSection/ExchangeSelectionRow/SelectedLeftLabel"
@onready var selected_team_label: Label = $"RootLayout/ExchangeSection/ExchangeSelectionRow/SelectedTeamLabel"
@onready var selected_right_label: Label = $"RootLayout/ExchangeSection/ExchangeSelectionRow/SelectedRightLabel"
@onready var submit_exchange_button: Button = $"RootLayout/ExchangeSection/ExchangeButtonRow/SubmitExchangeButton"
@onready var clear_exchange_button: Button = $"RootLayout/ExchangeSection/ExchangeButtonRow/ClearExchangeButton"
@onready var selected_play_label: Label = $"RootLayout/PlaySection/SelectedPlayLabel"
@onready var clear_play_selection_button: Button = $"RootLayout/PlaySection/PlaySelectionButtonRow/ClearPlaySelectionButton"
@onready var dragon_prompt_label: Label = $"RootLayout/DragonSection/DragonPromptLabel"
@onready var dragon_recipient_container: HBoxContainer = $"RootLayout/DragonSection/DragonRecipientContainer"
@onready var round_result_label: Label = $"RootLayout/ResultSection/RoundResultLabel"
@onready var hand_container: HBoxContainer = $"RootLayout/HandSection/HandContainer"
@onready var table_container: HBoxContainer = $"RootLayout/TableSection/TableContainer"

var api_client
var game_store
var pending_exchange_cards: Array = []
var pending_play_cards: Array = []


func _ready() -> void:
	api_client = ApiClientScript.new()
	game_store = GameStoreScript.new()
	add_child(api_client)
	add_child(game_store)

	api_client.health_checked.connect(_on_health_checked)
	api_client.game_created.connect(_on_game_created)
	api_client.snapshot_received.connect(_on_snapshot_received)
	api_client.grand_tichu_submitted.connect(_on_grand_tichu_submitted)
	api_client.exchange_submitted.connect(_on_exchange_submitted)
	api_client.small_tichu_submitted.connect(_on_small_tichu_submitted)
	api_client.play_submitted.connect(_on_play_submitted)
	api_client.pass_submitted.connect(_on_pass_submitted)
	api_client.dragon_recipient_submitted.connect(_on_dragon_recipient_submitted)

	create_game_button.pressed.connect(_on_create_game_pressed)
	refresh_button.pressed.connect(_on_refresh_pressed)
	pass_button.pressed.connect(_on_pass_pressed)
	play_button.pressed.connect(_on_play_pressed)
	small_tichu_button.pressed.connect(_on_small_tichu_pressed)
	grand_tichu_yes_button.pressed.connect(_on_grand_tichu_pressed.bind(true))
	grand_tichu_no_button.pressed.connect(_on_grand_tichu_pressed.bind(false))
	submit_exchange_button.pressed.connect(_on_submit_exchange_pressed)
	clear_exchange_button.pressed.connect(_on_clear_exchange_pressed)
	clear_play_selection_button.pressed.connect(_on_clear_play_selection_pressed)

	_setup_player_selects()
	viewer_select.item_selected.connect(_on_viewer_selected)
	actor_select.item_selected.connect(_on_actor_selected)

	render_buttons({})
	_reset_exchange_selection()
	_reset_play_selection()
	_render_hand_cards([])
	_render_cards(table_container, [])
	_render_dragon_recipient_options({})
	_render_round_result({})
	api_client.check_health()


func _on_health_checked(success: bool, payload: Dictionary) -> void:
	if success and payload.get("status", "") == "ok":
		status_label.text = "Server: connected"
		error_label.text = ""
		return

	status_label.text = "Server: error"
	show_error(_message_from_payload(payload, "health check failed"))


func _on_game_created(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "game creation failed"))
		return

	game_store.apply_snapshot(payload)
	game_store.set_selected_viewer(game_store.viewer)
	game_store.set_selected_actor(game_store.viewer)
	_select_option(viewer_select, game_store.selected_viewer)
	_select_option(actor_select, game_store.selected_actor)
	render_snapshot(payload)
	error_label.text = ""


func _on_snapshot_received(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "snapshot refresh failed"))
		return

	game_store.apply_snapshot(payload)
	render_snapshot(payload)
	error_label.text = ""


func _on_grand_tichu_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "grand tichu request failed"))
		return

	game_store.apply_snapshot(payload)
	render_snapshot(payload)
	error_label.text = ""


func _on_exchange_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "exchange request failed"))
		return

	game_store.apply_snapshot(payload)
	_reset_exchange_selection()
	render_snapshot(payload)
	error_label.text = ""


func _on_small_tichu_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "small tichu request failed"))
		return

	game_store.apply_snapshot(payload)
	render_snapshot(payload)
	error_label.text = ""


func _on_play_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "play request failed"))
		return

	game_store.apply_snapshot(payload)
	_reset_play_selection()
	render_snapshot(payload)
	error_label.text = ""


func _on_pass_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "pass request failed"))
		return

	game_store.apply_snapshot(payload)
	_reset_play_selection()
	render_snapshot(payload)
	error_label.text = ""


func _on_dragon_recipient_submitted(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "dragon recipient request failed"))
		return

	game_store.apply_snapshot(payload)
	render_snapshot(payload)
	error_label.text = ""


func _on_create_game_pressed() -> void:
	error_label.text = ""
	api_client.create_game()


func _on_refresh_pressed() -> void:
	if not game_store.has_active_game():
		show_error("No active game to refresh.")
		return

	error_label.text = ""
	api_client.get_snapshot(game_store.game_id, game_store.selected_viewer)


func _on_grand_tichu_pressed(declare: bool) -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return

	error_label.text = ""
	api_client.submit_grand_tichu(game_store.game_id, game_store.selected_actor, declare)


func _on_submit_exchange_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending exchange choices.")
		return
	if game_store.phase != "prepare_exchange":
		show_error("Exchange is only available during prepare_exchange.")
		return
	if game_store.selected_actor != game_store.selected_viewer:
		show_error("Set Viewer and Actor to the same player before selecting exchange cards.")
		return
	if pending_exchange_cards.size() != 3:
		show_error("Select exactly 3 cards for left, team, right.")
		return

	error_label.text = ""
	api_client.submit_exchange(
		game_store.game_id,
		game_store.selected_actor,
		pending_exchange_cards[0],
		pending_exchange_cards[1],
		pending_exchange_cards[2]
	)


func _on_clear_exchange_pressed() -> void:
	_reset_exchange_selection()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))


func _on_small_tichu_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if game_store.phase != "trick":
		show_error("Small Tichu is only available during trick.")
		return
	if game_store.selected_actor != game_store.selected_viewer:
		show_error("Set Viewer and Actor to the same player before declaring small tichu.")
		return
	if not game_store.available_actions.get("can_declare_small_tichu", false):
		show_error("Small Tichu is not available right now.")
		return

	error_label.text = ""
	api_client.submit_small_tichu(game_store.game_id, game_store.selected_actor)


func _on_play_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if game_store.phase != "trick":
		show_error("Play is only available during trick.")
		return
	if game_store.selected_actor != game_store.selected_viewer:
		show_error("Set Viewer and Actor to the same player before choosing play cards.")
		return
	if not _actor_is_current_turn():
		show_error("Selected actor is not the current player.")
		return
	if pending_play_cards.is_empty():
		show_error("Select at least one card to play.")
		return

	error_label.text = ""
	api_client.submit_play(game_store.game_id, game_store.selected_actor, pending_play_cards)


func _on_pass_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if game_store.phase != "trick":
		show_error("Pass is only available during trick.")
		return
	if not _actor_is_current_turn():
		show_error("Selected actor is not the current player.")
		return

	error_label.text = ""
	api_client.submit_pass(game_store.game_id, game_store.selected_actor)


func _on_clear_play_selection_pressed() -> void:
	_reset_play_selection()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))


func _on_dragon_recipient_pressed(recipient_index: int) -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if game_store.phase != "await_dragon_recipient":
		show_error("Dragon recipient is only available after a dragon trick is won.")
		return

	var winner_index: Variant = _dragon_winner_index()
	if winner_index == null:
		show_error("Dragon winner could not be determined.")
		return
	if game_store.selected_actor != int(winner_index):
		show_error("Set Actor to the dragon winner before choosing a recipient.")
		return
	if not _is_opponent_of(int(winner_index), recipient_index):
		show_error("Dragon recipient must be on the opposing team.")
		return

	error_label.text = ""
	api_client.submit_dragon_recipient(game_store.game_id, game_store.selected_actor, recipient_index)


func render_snapshot(snapshot: Dictionary) -> void:
	var state: Dictionary = snapshot.get("state", {})
	var table_state: Dictionary = state.get("table", {})
	var phase: String = str(snapshot.get("phase", "-"))

	phase_label.text = "Phase: %s" % phase
	game_info_label.text = _game_info_text(state.get("game", {}))
	var current_player = table_state.get("current_player_index", null)
	turn_label.text = "Turn: %s | Viewer: %d | Actor: %d" % [
		"-" if current_player == null else str(current_player),
		game_store.selected_viewer,
		game_store.selected_actor,
	]

	render_hand(state.get("viewer_hand", []))
	render_table(table_state)
	_render_dragon_recipient_options(snapshot)
	_render_round_result(snapshot.get("round_result", {}))
	if phase != "prepare_exchange":
		_reset_exchange_selection()
	if phase != "trick":
		_reset_play_selection()
	render_buttons(snapshot.get("available_actions", {}))


func render_hand(viewer_hand: Array) -> void:
	_render_hand_cards(viewer_hand)


func render_table(table_state: Dictionary) -> void:
	_render_cards(table_container, table_state.get("current_trick_cards", []))


func render_buttons(actions: Dictionary) -> void:
	refresh_button.disabled = not game_store.has_active_game()
	pass_button.disabled = not (
		game_store.has_active_game()
		and game_store.phase == "trick"
		and _actor_is_current_turn()
	)
	play_button.disabled = not (
		game_store.has_active_game()
		and game_store.phase == "trick"
		and game_store.selected_actor == game_store.selected_viewer
		and _actor_is_current_turn()
		and not pending_play_cards.is_empty()
	)
	small_tichu_button.disabled = not (
		game_store.has_active_game()
		and game_store.phase == "trick"
		and game_store.selected_actor == game_store.selected_viewer
		and actions.get("can_declare_small_tichu", false) == true
	)

	var can_grand_tichu: bool = game_store.has_active_game() and game_store.phase == "prepare_grand_tichu"
	grand_tichu_yes_button.disabled = not can_grand_tichu
	grand_tichu_no_button.disabled = not can_grand_tichu

	var can_exchange: bool = (
		game_store.has_active_game()
		and game_store.phase == "prepare_exchange"
		and game_store.selected_actor == game_store.selected_viewer
	)
	submit_exchange_button.disabled = not can_exchange or pending_exchange_cards.size() != 3
	clear_exchange_button.disabled = pending_exchange_cards.is_empty()
	clear_play_selection_button.disabled = pending_play_cards.is_empty()


func show_error(message: String) -> void:
	error_label.text = message
	push_warning(message)


func _render_cards(container: HBoxContainer, cards: Array) -> void:
	for child in container.get_children():
		child.queue_free()

	if cards.is_empty():
		var empty_label := Label.new()
		empty_label.text = "(empty)"
		container.add_child(empty_label)
		return

	for card_data in cards:
		var card_label := Label.new()
		card_label.text = _format_card(card_data)
		container.add_child(card_label)


func _render_hand_cards(cards: Array) -> void:
	for child in hand_container.get_children():
		child.queue_free()

	if cards.is_empty():
		var empty_label := Label.new()
		empty_label.text = "(empty)"
		hand_container.add_child(empty_label)
		return

	for card_data in cards:
		var card_button := Button.new()
		var card_text := _format_card(card_data)
		if _contains_card(pending_exchange_cards, card_data) or _contains_card(pending_play_cards, card_data):
			card_text = "[%s]" % card_text
		card_button.text = card_text
		card_button.disabled = not _can_interact_with_hand()
		card_button.pressed.connect(_on_hand_card_pressed.bind(card_data))
		hand_container.add_child(card_button)


func _render_dragon_recipient_options(snapshot: Dictionary) -> void:
	for child in dragon_recipient_container.get_children():
		child.queue_free()

	if snapshot.get("phase", "") != "await_dragon_recipient":
		dragon_prompt_label.text = "Dragon Recipient: -"
		var hidden_label := Label.new()
		hidden_label.text = "(not needed)"
		dragon_recipient_container.add_child(hidden_label)
		return

	var winner_index: Variant = _dragon_winner_index()
	if winner_index == null:
		dragon_prompt_label.text = "Dragon Recipient: unavailable"
		var unavailable_label := Label.new()
		unavailable_label.text = "(winner unknown)"
		dragon_recipient_container.add_child(unavailable_label)
		return

	dragon_prompt_label.text = "Dragon Recipient for Player %d" % int(winner_index)
	if game_store.selected_actor != int(winner_index):
		var info_label := Label.new()
		info_label.text = "Set Actor to Player %d to choose recipient." % int(winner_index)
		dragon_recipient_container.add_child(info_label)
		return

	for player_index in range(4):
		if not _is_opponent_of(int(winner_index), player_index):
			continue
		var recipient_button := Button.new()
		recipient_button.text = "Give to Player %d" % player_index
		recipient_button.pressed.connect(_on_dragon_recipient_pressed.bind(player_index))
		dragon_recipient_container.add_child(recipient_button)


func _render_round_result(round_result: Dictionary) -> void:
	if round_result.is_empty():
		round_result_label.text = "Round Result: -"
		return

	var deltas: Array = round_result.get("score_deltas", [])
	var players_out_order: Array = round_result.get("players_out_order", [])
	round_result_label.text = "Round Result: %s | Scores %s | Out %s" % [
		str(round_result.get("end_reason", "-")),
		str(deltas),
		str(players_out_order),
	]


func _game_info_text(game_state: Dictionary) -> String:
	var scores: Array = game_state.get("team_scores", [])
	return "Scores: %s | Round: %s" % [str(scores), str(game_state.get("round_index", "-"))]


func _format_card(card_data: Variant) -> String:
	if typeof(card_data) != TYPE_DICTIONARY:
		return str(card_data)

	var suit := str(card_data.get("suit", ""))
	var rank = card_data.get("rank", "?")
	return "%s-%s" % [suit if suit != "" else "SP", str(rank)]


func _message_from_payload(payload: Dictionary, fallback: String) -> String:
	var error_payload = payload.get("error", {})
	if typeof(error_payload) == TYPE_DICTIONARY:
		return str(error_payload.get("message", fallback))
	return fallback


func _setup_player_selects() -> void:
	for player_index in range(4):
		viewer_select.add_item("Viewer %d" % player_index, player_index)
		actor_select.add_item("Player %d" % player_index, player_index)
	_select_option(viewer_select, 0)
	_select_option(actor_select, 0)


func _on_viewer_selected(index: int) -> void:
	game_store.set_selected_viewer(viewer_select.get_item_id(index))
	_reset_exchange_selection()
	_reset_play_selection()
	if game_store.has_active_game():
		api_client.get_snapshot(game_store.game_id, game_store.selected_viewer)


func _on_actor_selected(index: int) -> void:
	game_store.set_selected_actor(actor_select.get_item_id(index))
	_reset_exchange_selection()
	_reset_play_selection()
	render_snapshot(
		{
			"phase": game_store.phase,
			"state": game_store.state,
			"available_actions": game_store.available_actions,
			"round_result": game_store.round_result,
		}
	)


func _select_option(button: OptionButton, value: int) -> void:
	for item_index in range(button.item_count):
		if button.get_item_id(item_index) == value:
			button.select(item_index)
			return


func _on_hand_card_pressed(card_data: Dictionary) -> void:
	if game_store.phase == "prepare_exchange":
		_handle_exchange_card(card_data)
		return
	if game_store.phase == "trick":
		_handle_play_card(card_data)


func _handle_exchange_card(card_data: Dictionary) -> void:
	if game_store.selected_actor != game_store.selected_viewer:
		show_error("Set Viewer and Actor to the same player before selecting exchange cards.")
		return
	if pending_exchange_cards.size() >= 3:
		show_error("Exchange already has 3 cards. Clear it to choose again.")
		return
	if _contains_card(pending_exchange_cards, card_data):
		show_error("That card is already selected.")
		return

	pending_exchange_cards.append(card_data.duplicate(true))
	_update_exchange_labels()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))
	error_label.text = ""


func _handle_play_card(card_data: Dictionary) -> void:
	if game_store.selected_actor != game_store.selected_viewer:
		show_error("Set Viewer and Actor to the same player before choosing play cards.")
		return
	if not _actor_is_current_turn():
		show_error("Selected actor is not the current player.")
		return

	if _contains_card(pending_play_cards, card_data):
		_remove_card(pending_play_cards, card_data)
	else:
		pending_play_cards.append(card_data.duplicate(true))

	_update_play_selection_label()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))
	error_label.text = ""


func _reset_exchange_selection() -> void:
	pending_exchange_cards.clear()
	_update_exchange_labels()


func _update_exchange_labels() -> void:
	selected_left_label.text = "Left: %s" % _exchange_slot_text(0)
	selected_team_label.text = "Team: %s" % _exchange_slot_text(1)
	selected_right_label.text = "Right: %s" % _exchange_slot_text(2)


func _exchange_slot_text(index: int) -> String:
	if index >= pending_exchange_cards.size():
		return "-"
	return _format_card(pending_exchange_cards[index])


func _reset_play_selection() -> void:
	pending_play_cards.clear()
	_update_play_selection_label()


func _update_play_selection_label() -> void:
	if pending_play_cards.is_empty():
		selected_play_label.text = "Selected: -"
		return

	var texts: Array[String] = []
	for card_data in pending_play_cards:
		texts.append(_format_card(card_data))
	selected_play_label.text = "Selected: %s" % ", ".join(texts)


func _actor_is_current_turn() -> bool:
	var table_state: Dictionary = game_store.state.get("table", {})
	return table_state.get("current_player_index", null) == game_store.selected_actor


func _dragon_winner_index() -> Variant:
	var table_state: Dictionary = game_store.state.get("table", {})
	return table_state.get("current_player_index", null)


func _can_interact_with_hand() -> bool:
	if game_store.selected_actor != game_store.selected_viewer:
		return false
	if game_store.phase == "prepare_exchange":
		return true
	if game_store.phase == "trick":
		return _actor_is_current_turn()
	return false


func _contains_card(cards: Array, target: Dictionary) -> bool:
	for existing_card in cards:
		if _cards_equal(existing_card, target):
			return true
	return false


func _remove_card(cards: Array, target: Dictionary) -> void:
	for index in range(cards.size()):
		if _cards_equal(cards[index], target):
			cards.remove_at(index)
			return


func _cards_equal(left: Dictionary, right: Dictionary) -> bool:
	return str(left.get("suit", "")) == str(right.get("suit", "")) and int(left.get("rank", -1)) == int(right.get("rank", -1))


func _is_opponent_of(player_index: int, other_player_index: int) -> bool:
	return (player_index % 2) != (other_player_index % 2)
