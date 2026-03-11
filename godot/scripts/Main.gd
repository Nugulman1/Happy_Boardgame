extends Control

const ApiClientScript = preload("res://scripts/ApiClient.gd")
const GameStoreScript = preload("res://scripts/GameStore.gd")
const SESSION_SAVE_PATH := "user://multiplayer_session.cfg"

@onready var status_label: Label = $"RootLayout/HeaderSection/StatusRow/StatusLabel"
@onready var phase_label: Label = $"RootLayout/HeaderSection/StatusRow/PhaseLabel"
@onready var turn_label: Label = $"RootLayout/HeaderSection/StatusRow/TurnLabel"
@onready var game_info_label: Label = $"RootLayout/HeaderSection/StatusRow/GameInfoLabel"
@onready var error_label: Label = $"RootLayout/HeaderSection/ErrorLabel"
@onready var lobby_section: VBoxContainer = $"RootLayout/LobbySection"
@onready var room_status_label: Label = $"RootLayout/LobbySection/RoomStatusLabel"
@onready var room_code_input: LineEdit = $"RootLayout/LobbySection/RoomControlsRow/RoomCodeInput"
@onready var create_room_button: Button = $"RootLayout/LobbySection/RoomControlsRow/CreateRoomButton"
@onready var start_room_button: Button = $"RootLayout/LobbySection/RoomControlsRow/StartRoomButton"
@onready var leave_room_button: Button = $"RootLayout/LobbySection/RoomControlsRow/LeaveRoomButton"
@onready var viewer_select: OptionButton = $"RootLayout/ControlSection/ControlRow/ViewerSelect"
@onready var actor_select: OptionButton = $"RootLayout/ControlSection/ControlRow/ActorSelect"
@onready var create_game_button: Button = $"RootLayout/ControlSection/ButtonRow/CreateGameButton"
@onready var control_row: HBoxContainer = $"RootLayout/ControlSection/ControlRow"
@onready var control_section: VBoxContainer = $"RootLayout/ControlSection"
@onready var content_row: HBoxContainer = $"RootLayout/ContentRow"
@onready var effects_section: VBoxContainer = $"RootLayout/EffectsSection"
@onready var refresh_button: Button = $"RootLayout/ControlSection/ButtonRow/RefreshButton"
@onready var pass_button: Button = $"RootLayout/ControlSection/ButtonRow/PassButton"
@onready var play_button: Button = $"RootLayout/ControlSection/ButtonRow/PlayButton"
@onready var small_tichu_button: Button = $"RootLayout/ControlSection/ButtonRow/SmallTichuButton"
@onready var grand_tichu_yes_button: Button = $"RootLayout/ControlSection/PrepareRow/GrandTichuYesButton"
@onready var grand_tichu_no_button: Button = $"RootLayout/ControlSection/PrepareRow/GrandTichuNoButton"
@onready var selected_left_label: Label = $"RootLayout/ContentRow/RightColumn/ExchangeSection/ExchangeSelectionRow/SelectedLeftLabel"
@onready var selected_team_label: Label = $"RootLayout/ContentRow/RightColumn/ExchangeSection/ExchangeSelectionRow/SelectedTeamLabel"
@onready var selected_right_label: Label = $"RootLayout/ContentRow/RightColumn/ExchangeSection/ExchangeSelectionRow/SelectedRightLabel"
@onready var submit_exchange_button: Button = $"RootLayout/ContentRow/RightColumn/ExchangeSection/ExchangeButtonRow/SubmitExchangeButton"
@onready var clear_exchange_button: Button = $"RootLayout/ContentRow/RightColumn/ExchangeSection/ExchangeButtonRow/ClearExchangeButton"
@onready var selected_play_label: Label = $"RootLayout/ContentRow/RightColumn/PlaySection/SelectedPlayLabel"
@onready var current_call_label: Label = $"RootLayout/ContentRow/RightColumn/PlaySection/CurrentCallLabel"
@onready var call_rank_select: OptionButton = $"RootLayout/ContentRow/RightColumn/PlaySection/CallRankRow/CallRankSelect"
@onready var clear_play_selection_button: Button = $"RootLayout/ContentRow/RightColumn/PlaySection/PlaySelectionButtonRow/ClearPlaySelectionButton"
@onready var dragon_prompt_label: Label = $"RootLayout/ContentRow/RightColumn/DragonSection/DragonPromptLabel"
@onready var dragon_recipient_container: HBoxContainer = $"RootLayout/ContentRow/RightColumn/DragonSection/DragonRecipientContainer"
@onready var round_result_label: Label = $"RootLayout/ContentRow/RightColumn/ResultSection/RoundResultLabel"
@onready var players_summary_label: Label = $"RootLayout/ContentRow/RightColumn/PlayersSection/PlayersSummaryLabel"
@onready var players_out_order_label: Label = $"RootLayout/ContentRow/RightColumn/PlayersSection/PlayersOutOrderLabel"
@onready var effects_label: Label = $"RootLayout/EffectsSection/EffectsLabel"
@onready var hand_container: HBoxContainer = $"RootLayout/ContentRow/LeftColumn/HandSection/HandContainer"
@onready var table_info_label: Label = $"RootLayout/ContentRow/LeftColumn/TableSection/TableInfoLabel"
@onready var table_container: HBoxContainer = $"RootLayout/ContentRow/LeftColumn/TableSection/TableContainer"
@onready var seat_buttons: Array[Button] = [
	$"RootLayout/LobbySection/SeatRow/Seat0Button",
	$"RootLayout/LobbySection/SeatRow/Seat1Button",
	$"RootLayout/LobbySection/SeatRow/Seat2Button",
	$"RootLayout/LobbySection/SeatRow/Seat3Button",
]

var api_client
var game_store
var pending_exchange_cards: Array = []
var pending_play_cards: Array = []
var legal_plays_loading := false
var legal_plays_error := ""
var play_preview_loading := false
var play_preview_error := ""
var play_preview_request_id := 0
var selected_call_rank = null
var recent_effect_lines: Array[String] = []
var http_status_message := "Server: checking..."
var socket_status_message := "Live: disconnected"
var restoring_session := false


func _ready() -> void:
	api_client = ApiClientScript.new()
	game_store = GameStoreScript.new()
	add_child(api_client)
	add_child(game_store)

	api_client.health_checked.connect(_on_health_checked)
	api_client.game_created.connect(_on_game_created)
	api_client.snapshot_received.connect(_on_snapshot_received)
	api_client.room_created.connect(_on_room_created)
	api_client.room_joined.connect(_on_room_joined)
	api_client.room_snapshot_loaded.connect(_on_room_snapshot_loaded)
	api_client.room_started.connect(_on_room_started)
	api_client.room_left.connect(_on_room_left)
	api_client.legal_plays_received.connect(_on_legal_plays_received)
	api_client.play_preview_received.connect(_on_play_preview_received)
	api_client.socket_snapshot_received.connect(_on_socket_snapshot_received)
	api_client.room_socket_snapshot_received.connect(_on_room_socket_snapshot_received)
	api_client.socket_action_result.connect(_on_socket_action_result)
	api_client.socket_action_error.connect(_on_socket_action_error)
	api_client.room_socket_error.connect(_on_room_socket_error)
	api_client.socket_connection_changed.connect(_on_socket_connection_changed)

	create_room_button.pressed.connect(_on_create_room_pressed)
	start_room_button.pressed.connect(_on_start_room_pressed)
	leave_room_button.pressed.connect(_on_leave_room_pressed)
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
	_setup_call_rank_select()
	viewer_select.item_selected.connect(_on_viewer_selected)
	actor_select.item_selected.connect(_on_actor_selected)
	call_rank_select.item_selected.connect(_on_call_rank_selected)
	for seat_index in range(seat_buttons.size()):
		seat_buttons[seat_index].pressed.connect(_on_join_seat_pressed.bind(seat_index))

	render_buttons({})
	_reset_exchange_selection()
	_reset_play_selection()
	_render_hand_cards([])
	_render_cards(table_container, [])
	_render_dragon_recipient_options({})
	_render_round_result({})
	create_game_button.visible = false
	control_row.visible = false
	viewer_select.disabled = true
	actor_select.disabled = true
	content_row.visible = false
	control_section.visible = false
	effects_section.visible = false
	_update_room_ui()
	_update_status_label()
	api_client.check_health()
	_try_restore_saved_session()


func _exit_tree() -> void:
	if api_client != null:
		api_client.disconnect_socket(false)


func _on_health_checked(success: bool, payload: Dictionary) -> void:
	if success and payload.get("status", "") == "ok":
		http_status_message = "Server: connected"
		_update_status_label()
		error_label.text = ""
		return

	http_status_message = "Server: error"
	_update_status_label()
	show_error(_message_from_payload(payload, "health check failed"))


func _on_game_created(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "game creation failed"))
		return

	recent_effect_lines.clear()
	game_store.apply_snapshot(payload)
	game_store.set_selected_viewer(game_store.viewer)
	game_store.set_selected_actor(game_store.viewer)
	_select_option(viewer_select, game_store.selected_viewer)
	_select_option(actor_select, game_store.selected_actor)
	render_snapshot(payload)
	api_client.connect_game_socket(game_store.game_id, game_store.selected_viewer)
	error_label.text = ""


func _on_snapshot_received(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "snapshot refresh failed"))
		return

	game_store.apply_snapshot(payload)
	render_snapshot(payload)
	error_label.text = ""


func _on_socket_snapshot_received(game_id: String, viewer: int, snapshot: Dictionary) -> void:
	if game_id != game_store.game_id or viewer != game_store.selected_viewer:
		return

	game_store.apply_snapshot(snapshot)
	render_snapshot(snapshot)
	error_label.text = ""


func _on_socket_connection_changed(connected: bool, message: String) -> void:
	socket_status_message = message
	_update_status_label()
	_update_room_ui()
	if game_store.has_active_game():
		render_buttons(game_store.available_actions)
	if connected:
		error_label.text = ""


func _on_socket_action_result(_request_id: int, action: String, _effects: Array) -> void:
	match action:
		"exchange":
			_reset_exchange_selection()
		"play", "pass":
			_reset_play_selection()

	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))
	_update_play_selection_label()
	error_label.text = ""


func _on_socket_action_error(_request_id: int, action: String, error_payload: Dictionary) -> void:
	var fallback := "%s request failed" % action if not action.is_empty() else "socket action failed"
	show_error(_message_from_payload({"error": error_payload}, fallback))


func _on_room_created(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "room creation failed"))
		return
	_apply_room_identity(payload)
	_apply_room_snapshot(payload.get("room_snapshot", {}))
	api_client.connect_room_socket(game_store.room_code, game_store.seat_token)
	error_label.text = ""


func _on_room_joined(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "room join failed"))
		return
	_apply_room_identity(payload)
	_apply_room_snapshot(payload.get("room_snapshot", {}))
	api_client.connect_room_socket(game_store.room_code, game_store.seat_token)
	error_label.text = ""


func _on_room_snapshot_loaded(success: bool, payload: Dictionary) -> void:
	restoring_session = false
	if not success:
		_clear_saved_session()
		show_error(_message_from_payload(payload, "saved room restore failed"))
		return
	_apply_room_identity(payload)
	_apply_room_snapshot(payload.get("room_snapshot", {}))
	_resume_room_or_game_socket()
	error_label.text = ""


func _on_room_started(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "room start failed"))
		return
	_apply_room_snapshot(payload.get("room_snapshot", {}))
	error_label.text = ""


func _on_room_left(success: bool, payload: Dictionary) -> void:
	if not success:
		show_error(_message_from_payload(payload, "leave room failed"))
		return
	api_client.disconnect_socket(false)
	if payload.get("room_closed", false):
		_clear_room_runtime()
	else:
		_clear_room_runtime()
	error_label.text = ""


func _on_room_socket_snapshot_received(room_code: String, snapshot: Dictionary) -> void:
	if room_code != game_store.room_code:
		return
	_apply_room_snapshot(snapshot)
	error_label.text = ""


func _on_room_socket_error(message: String) -> void:
	show_error(message)


func _on_create_room_pressed() -> void:
	if game_store.has_active_room():
		show_error("Leave the current room before creating a new one.")
		return
	error_label.text = ""
	api_client.create_room()


func _on_join_seat_pressed(seat_index: int) -> void:
	if game_store.has_active_room():
		show_error("Already joined a room.")
		return
	var room_code := room_code_input.text.strip_edges().to_upper()
	if room_code.is_empty():
		show_error("Enter a room code before joining a seat.")
		return
	error_label.text = ""
	api_client.join_room(room_code, seat_index)


func _on_start_room_pressed() -> void:
	if not game_store.has_active_room():
		show_error("Join a room before starting.")
		return
	error_label.text = ""
	api_client.start_room(game_store.room_code, game_store.seat_token)


func _on_leave_room_pressed() -> void:
	if not game_store.has_active_room():
		show_error("No active room to leave.")
		return
	error_label.text = ""
	api_client.leave_room(game_store.room_code, game_store.seat_token)


func _on_create_game_pressed() -> void:
	error_label.text = ""
	api_client.create_game()


func _on_refresh_pressed() -> void:
	if not game_store.has_active_game():
		show_error("No active game to refresh.")
		return

	error_label.text = ""
	api_client.get_snapshot(game_store.game_id, game_store.selected_viewer, game_store.seat_token)


func _on_grand_tichu_pressed(declare: bool) -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if not game_store.available_actions.get("can_declare_grand_tichu", false):
		show_error("Grand Tichu is not available right now.")
		return
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"grand_tichu",
		{
			"player_index": game_store.selected_actor,
			"declare": declare,
		}
	)


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
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"exchange",
		{
			"player_index": game_store.selected_actor,
			"to_left": pending_exchange_cards[0],
			"to_team": pending_exchange_cards[1],
			"to_right": pending_exchange_cards[2],
		}
	)


func _on_clear_exchange_pressed() -> void:
	_reset_exchange_selection()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))


func _on_small_tichu_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if not game_store.available_actions.get("can_declare_small_tichu", false):
		show_error("Small Tichu is not available right now.")
		return
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"small_tichu",
		{
			"player_index": game_store.selected_actor,
		}
	)


func _on_play_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if not game_store.available_actions.get("can_play", false):
		show_error("Play is not available right now.")
		return
	if pending_play_cards.is_empty():
		show_error("Select at least one card to play.")
		return
	if play_preview_loading:
		show_error("Play preview is still loading.")
		return
	if not game_store.play_preview.get("can_submit_play", false):
		show_error(str(game_store.play_preview.get("message", "Selected cards cannot be played right now.")))
		return
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"play",
		{
			"player_index": game_store.selected_actor,
			"cards": pending_play_cards,
			"call_rank": _selected_call_rank_payload(),
		}
	)


func _on_pass_pressed() -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if not game_store.available_actions.get("can_pass", false):
		show_error("Pass is not available right now.")
		return
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"pass",
		{
			"player_index": game_store.selected_actor,
		}
	)


func _on_clear_play_selection_pressed() -> void:
	_reset_play_selection()
	render_buttons(game_store.available_actions)
	_render_hand_cards(game_store.state.get("viewer_hand", []))


func _on_dragon_recipient_pressed(recipient_index: int) -> void:
	if not game_store.has_active_game():
		show_error("Create a game before sending actions.")
		return
	if not game_store.available_actions.get("can_choose_dragon_recipient", false):
		show_error("Dragon recipient is not available right now.")
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
	if not _ensure_live_action_socket():
		return

	error_label.text = ""
	api_client.send_action(
		"dragon_recipient",
		{
			"player_index": game_store.selected_actor,
			"recipient_index": recipient_index,
		}
	)


func _on_legal_plays_received(success: bool, game_id: String, viewer: int, payload: Dictionary) -> void:
	if game_id != game_store.game_id or viewer != game_store.selected_viewer:
		return

	legal_plays_loading = false
	if not success:
		game_store.clear_legal_plays()
		legal_plays_error = _message_from_payload(payload, "legal plays request failed")
		_update_play_selection_label()
		return

	game_store.set_legal_plays(payload.get("plays", []))
	legal_plays_error = ""
	_update_play_selection_label()


func _on_play_preview_received(
	success: bool,
	game_id: String,
	viewer: int,
	request_id: int,
	payload: Dictionary
) -> void:
	if request_id != play_preview_request_id:
		return
	if game_id != game_store.game_id or viewer != game_store.selected_viewer:
		return
	if pending_play_cards.is_empty():
		return

	play_preview_loading = false
	if not success:
		game_store.clear_play_preview()
		play_preview_error = _message_from_payload(payload, "play preview request failed")
		render_buttons(game_store.available_actions)
		_update_play_selection_label()
		return

	game_store.set_play_preview(payload)
	play_preview_error = ""
	render_buttons(game_store.available_actions)
	_update_play_selection_label()


func render_snapshot(snapshot: Dictionary, refresh_helpers: bool = true) -> void:
	var state: Dictionary = snapshot.get("state", {})
	var table_state: Dictionary = state.get("table", {})
	var phase: String = str(snapshot.get("phase", "-"))

	_append_effects(snapshot.get("effects", []))
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
	_render_table_info(table_state)
	_render_players_summary(state.get("players", []))
	_render_players_out_order(state.get("players_out_order", []))
	_render_effects()
	_render_dragon_recipient_options(snapshot)
	_render_round_result(snapshot.get("round_result", {}))
	if phase != "prepare_exchange":
		_reset_exchange_selection()
	if phase != "trick":
		_reset_play_selection()
	render_buttons(snapshot.get("available_actions", {}))
	_update_call_rank_ui()
	if refresh_helpers:
		_sync_legal_plays(snapshot)
		_sync_play_preview()
	_update_play_selection_label()


func render_hand(viewer_hand: Array) -> void:
	_render_hand_cards(viewer_hand)


func render_table(table_state: Dictionary) -> void:
	_render_cards(table_container, table_state.get("current_trick_cards", []))


func _render_table_info(table_state: Dictionary) -> void:
	var leader_index = table_state.get("leader_index", null)
	var trick_index = table_state.get("trick_index", null)
	table_info_label.text = "Leader: %s | Trick: %s" % [
		"-" if leader_index == null else str(leader_index),
		"-" if trick_index == null else str(trick_index),
	]


func render_buttons(actions: Dictionary) -> void:
	refresh_button.disabled = not game_store.has_active_game()
	var live_game_socket: bool = api_client.is_socket_connected_for(game_store.game_id, game_store.selected_viewer)
	pass_button.disabled = not (game_store.has_active_game() and live_game_socket and actions.get("can_pass", false) == true)
	play_button.disabled = not (
		game_store.has_active_game()
		and live_game_socket
		and actions.get("can_play", false) == true
		and not pending_play_cards.is_empty()
		and not play_preview_loading
		and game_store.play_preview.get("can_submit_play", false) == true
	)
	small_tichu_button.disabled = not (
		game_store.has_active_game()
		and live_game_socket
		and actions.get("can_declare_small_tichu", false) == true
	)

	var can_grand_tichu: bool = (
		game_store.has_active_game()
		and live_game_socket
		and actions.get("can_declare_grand_tichu", false) == true
	)
	grand_tichu_yes_button.disabled = not can_grand_tichu
	grand_tichu_no_button.disabled = not can_grand_tichu

	var can_exchange: bool = (
		game_store.has_active_game()
		and live_game_socket
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

	var actions: Dictionary = snapshot.get("available_actions", {})
	if not actions.get("can_choose_dragon_recipient", false):
		dragon_prompt_label.text = "Dragon Recipient: -"
		var hidden_label := Label.new()
		hidden_label.text = "(not available)"
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


func _render_players_summary(players: Array) -> void:
	if players.is_empty():
		players_summary_label.text = "Players: -"
		return

	var lines: Array[String] = []
	for player_data in players:
		if typeof(player_data) != TYPE_DICTIONARY:
			lines.append(str(player_data))
			continue
		var player_index = int(player_data.get("player_index", -1))
		var hand_count = int(player_data.get("hand_count", 0))
		var status := "out" if player_data.get("is_out", false) else "active"
		var grand := "grand" if player_data.get("declared_grand_tichu", false) else "no grand"
		var small := "small" if player_data.get("declared_small_tichu", false) else "no small"
		lines.append("P%d | hand %d | %s | %s | %s" % [player_index, hand_count, status, grand, small])
	players_summary_label.text = "Players:\n%s" % "\n".join(lines)


func _render_players_out_order(players_out_order: Array) -> void:
	if players_out_order.is_empty():
		players_out_order_label.text = "Out Order: -"
		return
	var order_parts: Array[String] = []
	for player_index in players_out_order:
		order_parts.append("P%s" % str(player_index))
	players_out_order_label.text = "Out Order: %s" % " -> ".join(order_parts)


func _render_effects() -> void:
	if recent_effect_lines.is_empty():
		effects_label.text = "Effects: -"
		return
	effects_label.text = "Effects:\n%s" % "\n".join(recent_effect_lines)


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


func _append_effects(effects: Array) -> void:
	if effects.is_empty():
		return
	for effect in effects:
		recent_effect_lines.append(_format_effect(effect))
	while recent_effect_lines.size() > 12:
		recent_effect_lines.remove_at(0)


func _format_effect(effect: Variant) -> String:
	if typeof(effect) != TYPE_DICTIONARY:
		return str(effect)

	var effect_dict: Dictionary = effect
	var effect_type := str(effect_dict.get("type", "effect"))
	var keys: Array = effect_dict.keys()
	keys.sort()
	var detail_parts: Array[String] = []
	for key in keys:
		if key == "type":
			continue
		detail_parts.append("%s=%s" % [str(key), _format_effect_value(effect_dict.get(key))])
	if detail_parts.is_empty():
		return effect_type
	return "%s | %s" % [effect_type, ", ".join(detail_parts)]


func _format_effect_value(value: Variant) -> String:
	if typeof(value) == TYPE_ARRAY:
		var parts: Array[String] = []
		for item in value:
			if typeof(item) == TYPE_DICTIONARY and item.has("rank"):
				parts.append(_format_card(item))
			else:
				parts.append(str(item))
		return "[%s]" % ", ".join(parts)
	if typeof(value) == TYPE_DICTIONARY and value.has("rank"):
		return _format_card(value)
	return str(value)


func _setup_player_selects() -> void:
	for player_index in range(4):
		viewer_select.add_item("Viewer %d" % player_index, player_index)
		actor_select.add_item("Player %d" % player_index, player_index)
	_select_option(viewer_select, 0)
	_select_option(actor_select, 0)


func _setup_call_rank_select() -> void:
	call_rank_select.clear()
	call_rank_select.add_item("None", -1)
	for rank in range(2, 15):
		call_rank_select.add_item(str(rank), rank)
	call_rank_select.select(0)
	call_rank_select.disabled = true


func _on_viewer_selected(index: int) -> void:
	game_store.set_selected_viewer(viewer_select.get_item_id(index))
	_reset_exchange_selection()
	_reset_play_selection()
	game_store.clear_legal_plays()
	legal_plays_loading = false
	legal_plays_error = ""
	_reset_play_preview()
	if game_store.has_active_game():
		api_client.connect_game_socket(game_store.game_id, game_store.selected_viewer)


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
		},
		false
	)


func _select_option(button: OptionButton, value: int) -> void:
	for item_index in range(button.item_count):
		if button.get_item_id(item_index) == value:
			button.select(item_index)
			return


func _update_status_label() -> void:
	status_label.text = "%s | %s" % [http_status_message, socket_status_message]


func _apply_room_identity(payload: Dictionary) -> void:
	game_store.set_multiplayer_identity(
		str(payload.get("room_code", "")),
		int(payload.get("seat_index", -1)),
		str(payload.get("seat_token", ""))
	)
	room_code_input.text = game_store.room_code
	_save_multiplayer_session()


func _apply_room_snapshot(snapshot: Dictionary) -> void:
	if typeof(snapshot) != TYPE_DICTIONARY or snapshot.is_empty():
		return
	game_store.apply_room_snapshot(snapshot)
	_update_room_ui()
	if game_store.room_status == "in_game" and not game_store.game_id.is_empty():
		_resume_room_or_game_socket()
	else:
		control_section.visible = false
		content_row.visible = false
		effects_section.visible = false


func _resume_room_or_game_socket() -> void:
	if not game_store.has_active_room():
		return
	if game_store.room_status == "lobby":
		api_client.connect_room_socket(game_store.room_code, game_store.seat_token)
		control_section.visible = false
		content_row.visible = false
		effects_section.visible = false
		return

	if game_store.room_status == "in_game" or game_store.room_status == "finished":
		api_client.connect_game_socket(game_store.game_id, game_store.selected_viewer, game_store.seat_token)
		api_client.get_snapshot(game_store.game_id, game_store.selected_viewer, game_store.seat_token)
		control_section.visible = true
		content_row.visible = true
		effects_section.visible = true


func _update_room_ui() -> void:
	if not game_store.has_active_room():
		room_status_label.text = "Room: -"
		start_room_button.disabled = true
		leave_room_button.disabled = true
		for seat_index in range(seat_buttons.size()):
			seat_buttons[seat_index].text = "Seat %d" % seat_index
			seat_buttons[seat_index].disabled = false
		return

	var snapshot: Dictionary = game_store.room_snapshot
	var seats: Array = snapshot.get("seats", [])
	room_status_label.text = "Room %s | Status %s | Seat %d" % [
		game_store.room_code,
		game_store.room_status,
		game_store.my_seat_index,
	]
	start_room_button.disabled = not bool(snapshot.get("can_start", false))
	leave_room_button.disabled = game_store.room_status != "lobby"
	for seat_index in range(seat_buttons.size()):
		var seat_data: Dictionary = seats[seat_index] if seat_index < seats.size() else {}
		var claimed := bool(seat_data.get("claimed", false))
		var connected := bool(seat_data.get("connected", false))
		var mine: bool = seat_index == game_store.my_seat_index
		var status_text := "open"
		if claimed:
			status_text = "connected" if connected else "claimed"
		seat_buttons[seat_index].text = "Seat %d | %s%s" % [
			seat_index,
			status_text,
			" | me" if mine else "",
		]
		seat_buttons[seat_index].disabled = claimed or game_store.room_status != "lobby" or mine


func _save_multiplayer_session() -> void:
	if not game_store.has_active_room():
		return
	var config := ConfigFile.new()
	config.set_value("session", "room_code", game_store.room_code)
	config.set_value("session", "seat_index", game_store.my_seat_index)
	config.set_value("session", "seat_token", game_store.seat_token)
	config.save(SESSION_SAVE_PATH)


func _clear_saved_session() -> void:
	var dir := DirAccess.open("user://")
	if dir != null and dir.file_exists("multiplayer_session.cfg"):
		dir.remove("multiplayer_session.cfg")


func _try_restore_saved_session() -> void:
	var config := ConfigFile.new()
	var load_error := config.load(SESSION_SAVE_PATH)
	if load_error != OK:
		return
	var room_code := str(config.get_value("session", "room_code", ""))
	var seat_token := str(config.get_value("session", "seat_token", ""))
	if room_code.is_empty() or seat_token.is_empty():
		_clear_saved_session()
		return
	restoring_session = true
	room_code_input.text = room_code
	api_client.get_room_state(room_code, seat_token)


func _clear_room_runtime() -> void:
	game_store.clear_multiplayer_identity()
	room_code_input.text = ""
	recent_effect_lines.clear()
	_render_effects()
	phase_label.text = "Phase: -"
	turn_label.text = "Turn: -"
	game_info_label.text = "Scores: - | Round: -"
	control_section.visible = false
	content_row.visible = false
	effects_section.visible = false
	_render_hand_cards([])
	_render_cards(table_container, [])
	_render_round_result({})
	_render_players_summary([])
	_render_players_out_order([])
	_render_dragon_recipient_options({})
	_update_room_ui()
	_clear_saved_session()


func _ensure_live_action_socket() -> bool:
	if api_client.is_socket_connected_for(game_store.game_id, game_store.selected_viewer):
		return true
	show_error("Live socket is not connected for the selected viewer.")
	return false


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
	if not game_store.available_actions.get("can_play", false):
		show_error("Play is not available right now.")
		return

	if _contains_card(pending_play_cards, card_data):
		_remove_card(pending_play_cards, card_data)
	else:
		pending_play_cards.append(card_data.duplicate(true))

	_update_call_rank_ui()
	_update_play_selection_label()
	_sync_play_preview()
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
	_reset_selected_call_rank()
	_update_call_rank_ui()
	_reset_play_preview()
	_update_play_selection_label()


func _update_play_selection_label() -> void:
	var helper_text := _play_selection_helper_text()
	if pending_play_cards.is_empty():
		selected_play_label.text = "Selected: -"
		if not helper_text.is_empty():
			selected_play_label.text += " | %s" % helper_text
		return

	var texts: Array[String] = []
	for card_data in pending_play_cards:
		texts.append(_format_card(card_data))
	selected_play_label.text = "Selected: %s" % ", ".join(texts)
	if not helper_text.is_empty():
		selected_play_label.text += " | %s" % helper_text


func _on_call_rank_selected(index: int) -> void:
	var item_id := call_rank_select.get_item_id(index)
	if item_id < 0:
		selected_call_rank = null
	else:
		selected_call_rank = item_id
	_update_call_rank_ui()
	_update_play_selection_label()
	_sync_play_preview()
	render_buttons(game_store.available_actions)
	error_label.text = ""


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
		return game_store.available_actions.get("can_play", false)
	return false


func _sync_legal_plays(snapshot: Dictionary) -> void:
	var state: Dictionary = snapshot.get("state", {})
	var table_state: Dictionary = state.get("table", {})
	var actions: Dictionary = snapshot.get("available_actions", {})
	var phase := str(snapshot.get("phase", ""))
	var call_rank = table_state.get("mahjong_call_rank", null)

	if phase != "trick" or call_rank == null or actions.get("can_play", false) != true:
		game_store.clear_legal_plays()
		legal_plays_loading = false
		legal_plays_error = ""
		return

	game_store.clear_legal_plays()
	legal_plays_loading = true
	legal_plays_error = ""
	api_client.get_legal_plays(game_store.game_id, game_store.selected_viewer, game_store.seat_token)


func _sync_play_preview() -> void:
	if pending_play_cards.is_empty():
		_reset_play_preview()
		return
	if not game_store.has_active_game() or game_store.available_actions.get("can_play", false) != true:
		_reset_play_preview()
		return

	play_preview_request_id += 1
	play_preview_loading = true
	play_preview_error = ""
	game_store.clear_play_preview()
	api_client.preview_play(
		game_store.game_id,
		game_store.selected_viewer,
		pending_play_cards,
		_selected_call_rank_payload(),
		play_preview_request_id,
		game_store.seat_token
	)


func _reset_play_preview() -> void:
	play_preview_loading = false
	play_preview_error = ""
	play_preview_request_id += 1
	game_store.clear_play_preview()


func _play_selection_helper_text() -> String:
	var preview_text := _play_preview_text()
	var table_state: Dictionary = game_store.state.get("table", {})
	var call_rank = table_state.get("mahjong_call_rank", null)
	var texts: Array[String] = []
	var selected_call_rank_payload = _selected_call_rank_payload()
	if not preview_text.is_empty():
		texts.append(preview_text)
	if _selection_contains_mahjong() and selected_call_rank_payload != null:
		texts.append("Call rank %s" % str(selected_call_rank_payload))
	if game_store.phase == "trick" and call_rank != null:
		if legal_plays_loading:
			texts.append("Mahjong call %s | loading legal plays..." % str(call_rank))
		elif not legal_plays_error.is_empty():
			texts.append("Mahjong call %s | legal plays unavailable" % str(call_rank))
		else:
			texts.append("Mahjong call %s | legal plays %d" % [str(call_rank), game_store.legal_plays.size()])
	return " | ".join(texts)


func _play_preview_text() -> String:
	if pending_play_cards.is_empty():
		return ""
	if play_preview_loading:
		return "Preview: loading..."
	if not play_preview_error.is_empty():
		return "Preview: unavailable"
	if game_store.play_preview.is_empty():
		return ""

	var parts: Array[String] = []
	var combo_type = game_store.play_preview.get("combo_type", null)
	if combo_type == null:
		parts.append("illegal shape")
	else:
		parts.append(str(combo_type))
	if game_store.play_preview.get("is_bomb", false):
		parts.append("bomb")
	if game_store.play_preview.get("beats_current_trick", false):
		parts.append("beats current trick")
	elif game_store.play_preview.get("is_legal_shape", false):
		parts.append("does not beat current trick")
	if not game_store.play_preview.get("satisfies_mahjong_call", true):
		parts.append("fails mahjong call")
	if not game_store.play_preview.get("can_submit_play", false):
		var preview_message := str(game_store.play_preview.get("message", ""))
		if not preview_message.is_empty() and preview_message != "selected cards do not beat the current trick":
			parts.append(preview_message)
	return "Preview: %s" % ", ".join(parts)


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


func _update_call_rank_ui() -> void:
	var table_state: Dictionary = game_store.state.get("table", {})
	var active_call_rank = table_state.get("mahjong_call_rank", null)
	if active_call_rank == null:
		current_call_label.text = "Current Call: -"
	else:
		current_call_label.text = "Current Call: %s" % str(active_call_rank)

	var can_select_call_rank: bool = (
		game_store.has_active_game()
		and game_store.phase == "trick"
		and _selection_contains_mahjong()
	)
	if not can_select_call_rank:
		_reset_selected_call_rank()
	call_rank_select.disabled = not can_select_call_rank
	_select_call_rank_value(_selected_call_rank_payload())


func _selected_call_rank_payload():
	return selected_call_rank


func _selection_contains_mahjong() -> bool:
	for card_data in pending_play_cards:
		if int(card_data.get("rank", -1)) == 1:
			return true
	return false


func _reset_selected_call_rank() -> void:
	selected_call_rank = null
	_select_call_rank_value(null)


func _select_call_rank_value(call_rank) -> void:
	var target_id := -1 if call_rank == null else int(call_rank)
	for item_index in range(call_rank_select.item_count):
		if call_rank_select.get_item_id(item_index) == target_id:
			call_rank_select.select(item_index)
			return
