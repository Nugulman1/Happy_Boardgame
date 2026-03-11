extends Control

const ApiClientScript = preload("res://scripts/ApiClient.gd")
const GameStoreScript = preload("res://scripts/GameStore.gd")
const PresentationBusScript = preload("res://scripts/PresentationBus.gd")
const EffectInterpreterScript = preload("res://scripts/EffectInterpreter.gd")
const SESSION_SAVE_PATH := "user://multiplayer_session.cfg"
const SCREEN_MODE_IDLE := "idle"
const SCREEN_MODE_LOBBY := "lobby"
const SCREEN_MODE_IN_GAME := "in_game"
const SCREEN_MODE_FINISHED := "finished"
const SCREEN_MODE_RESTORING := "restoring"

@onready var app_shell: VBoxContainer = $"RootLayout/AppShell"
@onready var body_row: HBoxContainer = $"RootLayout/AppShell/BodyRow"
@onready var status_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/StatusRow/StatusLabel"
@onready var phase_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/StatusRow/PhaseLabel"
@onready var turn_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/StatusRow/TurnLabel"
@onready var game_info_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/StatusRow/GameInfoLabel"
@onready var error_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/ErrorLabel"
@onready var announcement_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/AnnouncementLabel"
@onready var screen_hint_label: Label = $"RootLayout/AppShell/HeaderSection/HeaderPadding/HeaderRows/ScreenHintLabel"
@onready var declaration_banner: PanelContainer = $"DeclarationBanner"
@onready var declaration_banner_title_label: Label = $"DeclarationBanner/BannerContent/BannerRows/BannerTitleLabel"
@onready var declaration_banner_subtitle_label: Label = $"DeclarationBanner/BannerContent/BannerRows/BannerSubtitleLabel"
@onready var sidebar_column: VBoxContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn"
@onready var lobby_section: VBoxContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection"
@onready var room_status_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomStatusLabel"
@onready var room_hint_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomHintLabel"
@onready var room_code_input: LineEdit = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomControlsRow/RoomCodeInput"
@onready var create_room_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomControlsRow/CreateRoomButton"
@onready var start_room_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomControlsRow/StartRoomButton"
@onready var leave_room_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/RoomControlsRow/LeaveRoomButton"
@onready var seat_row: GridContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/SeatRow"
@onready var viewer_select: OptionButton = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ControlRow/ViewerSelect"
@onready var actor_select: OptionButton = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ControlRow/ActorSelect"
@onready var create_game_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/CreateGameButton"
@onready var control_row: HBoxContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ControlRow"
@onready var control_section: VBoxContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection"
@onready var control_button_row: GridContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow"
@onready var control_hint_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ControlHintLabel"
@onready var action_hint_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ActionHintLabel"
@onready var effects_section: VBoxContainer = $"RootLayout/AppShell/BodyRow/SidebarColumn/EffectsCard/EffectsPadding/EffectsSection"
@onready var refresh_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/RefreshButton"
@onready var pass_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/PassButton"
@onready var play_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/PlayButton"
@onready var small_tichu_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/SmallTichuButton"
@onready var grand_tichu_yes_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/GrandTichuYesButton"
@onready var grand_tichu_no_button: Button = $"RootLayout/AppShell/BodyRow/SidebarColumn/DevCard/DevPadding/ControlSection/ButtonRow/GrandTichuNoButton"
@onready var play_stage_hint_label: Label = $"RootLayout/AppShell/BodyRow/PlayStageCard/PlayStagePadding/PlayStage/StageHeaderRow/PlayStageHintLabel"
@onready var hand_hint_label: Label = $"RootLayout/AppShell/BodyRow/PlayStageCard/PlayStagePadding/PlayStage/HandSection/HandHeaderRow/HandHintLabel"
@onready var context_column: VBoxContainer = $"RootLayout/AppShell/BodyRow/ContextColumn"
@onready var selected_left_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeSelectionRow/SelectedLeftLabel"
@onready var selected_team_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeSelectionRow/SelectedTeamLabel"
@onready var selected_right_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeSelectionRow/SelectedRightLabel"
@onready var exchange_hint_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeHintLabel"
@onready var submit_exchange_button: Button = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeButtonRow/SubmitExchangeButton"
@onready var clear_exchange_button: Button = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/ExchangeSection/ExchangeButtonRow/ClearExchangeButton"
@onready var selected_play_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/PlaySection/SelectedPlayLabel"
@onready var selection_hint_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/PlaySection/SelectionHintLabel"
@onready var current_call_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/PlaySection/CurrentCallLabel"
@onready var call_rank_select: OptionButton = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/PlaySection/CallRankRow/CallRankSelect"
@onready var clear_play_selection_button: Button = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/PlaySection/PlaySelectionButtonRow/ClearPlaySelectionButton"
@onready var dragon_prompt_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/DragonSection/DragonPromptLabel"
@onready var dragon_recipient_container: HBoxContainer = $"RootLayout/AppShell/BodyRow/ContextColumn/ActionCard/ActionPadding/ActionSection/DragonSection/DragonRecipientContainer"
@onready var round_result_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ResultCard/ResultPadding/ResultSection/RoundResultLabel"
@onready var players_out_order_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersOutOrderLabel"
@onready var players_grid: GridContainer = $"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid"
@onready var effects_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/EffectsCard/EffectsPadding/EffectsSection/EffectsLabel"
@onready var hand_container: HBoxContainer = $"RootLayout/AppShell/BodyRow/PlayStageCard/PlayStagePadding/PlayStage/HandSection/HandFrame/HandPadding/HandContainer"
@onready var table_info_label: Label = $"RootLayout/AppShell/BodyRow/PlayStageCard/PlayStagePadding/PlayStage/TableSection/TableInfoLabel"
@onready var table_motion_label: Label = $"RootLayout/AppShell/BodyRow/SidebarColumn/EffectsCard/EffectsPadding/EffectsSection/TableMotionLabel"
@onready var table_container: HBoxContainer = $"RootLayout/AppShell/BodyRow/PlayStageCard/PlayStagePadding/PlayStage/TableSection/TableCardFrame/TableCardPadding/TableContainer"
@onready var score_summary_label: Label = $"RootLayout/AppShell/BodyRow/ContextColumn/ResultCard/ResultPadding/ResultSection/ScoreSummaryLabel"
@onready var result_overlay: PanelContainer = $"ResultOverlay"
@onready var result_overlay_title_label: Label = $"ResultOverlay/OverlayContent/OverlayRows/OverlayTitleLabel"
@onready var result_overlay_body_label: Label = $"ResultOverlay/OverlayContent/OverlayRows/OverlayBodyLabel"
@onready var player_panel_containers: Array[PanelContainer] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3",
]
@onready var player_turn_highlights: Array[ColorRect] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/TurnHighlight",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/TurnHighlight",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/TurnHighlight",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/TurnHighlight",
]
@onready var player_name_labels: Array[Label] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/NameLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/NameLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/NameLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/NameLabel",
]
@onready var player_hand_labels: Array[Label] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/HandLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/HandLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/HandLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/HandLabel",
]
@onready var player_status_labels: Array[Label] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/StatusLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/StatusLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/StatusLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/StatusLabel",
]
@onready var player_badge_labels: Array[Label] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/BadgeLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/BadgeLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/BadgeLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/BadgeLabel",
]
@onready var player_portrait_slots: Array[PanelContainer] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/PortraitSlot",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/PortraitSlot",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/PortraitSlot",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/PortraitSlot",
]
@onready var player_portrait_labels: Array[Label] = [
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel0/Content/Rows/PortraitSlot/PortraitCenter/PortraitLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel1/Content/Rows/PortraitSlot/PortraitCenter/PortraitLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel2/Content/Rows/PortraitSlot/PortraitCenter/PortraitLabel",
	$"RootLayout/AppShell/BodyRow/ContextColumn/PlayersCard/PlayersPadding/PlayersSection/PlayersGrid/PlayerPanel3/Content/Rows/PortraitSlot/PortraitCenter/PortraitLabel",
]
@onready var seat_buttons: Array[Button] = [
	$"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/SeatRow/Seat0Button",
	$"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/SeatRow/Seat1Button",
	$"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/SeatRow/Seat2Button",
	$"RootLayout/AppShell/BodyRow/SidebarColumn/LobbyCard/LobbyPadding/LobbySection/SeatRow/Seat3Button",
]

var api_client
var game_store
var presentation_bus
var effect_interpreter
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
var presented_turn_highlight_player = null
var announcement_text := ""
var table_motion_text := ""
var score_summary_text := ""
var announcement_deadline_msec := 0
var table_motion_deadline_msec := 0
var score_summary_deadline_msec := 0
var current_presentation_event_requires_async_ack := false
var portrait_state_by_player: Array[String] = ["base", "base", "base", "base"]
var portrait_state_deadline_msec: Array[int] = [0, 0, 0, 0]


func _ready() -> void:
	api_client = ApiClientScript.new()
	game_store = GameStoreScript.new()
	presentation_bus = PresentationBusScript.new()
	effect_interpreter = EffectInterpreterScript.new()
	add_child(api_client)
	add_child(game_store)
	add_child(presentation_bus)
	add_child(effect_interpreter)

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
	presentation_bus.presentation_event_started.connect(_on_presentation_event_started)

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

	var viewport := get_viewport()
	if viewport != null and not viewport.size_changed.is_connected(_on_viewport_size_changed):
		viewport.size_changed.connect(_on_viewport_size_changed)

	render_buttons({})
	_reset_exchange_selection()
	_reset_play_selection()
	_render_hand_cards([])
	_render_cards(table_container, [])
	_refresh_announcement_label()
	_refresh_table_motion_label()
	_refresh_score_summary_label()
	_render_players_summary([])
	for player_index in range(player_portrait_labels.size()):
		set_player_portrait_placeholder(player_index)
	_render_dragon_recipient_options({})
	_render_round_result({})
	create_game_button.visible = true
	control_row.visible = true
	viewer_select.disabled = false
	actor_select.disabled = false
	_update_room_ui()
	_apply_responsive_layout()
	_refresh_screen_mode()
	_refresh_room_hint()
	_refresh_action_feedback({})
	_update_status_label()
	api_client.check_health()
	_try_restore_saved_session()


func _process(_delta: float) -> void:
	_expire_presentation_state()


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

	presentation_bus.clear()
	presented_turn_highlight_player = null
	_clear_presentation_overlays()
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
	else:
		_refresh_action_feedback({})
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


func _on_presentation_event_started(event: Dictionary) -> void:
	current_presentation_event_requires_async_ack = false
	var event_name := str(event.get("name", ""))
	match event_name:
		"announce_grand_tichu", "announce_small_tichu":
			_apply_announcement_event(event)
		"announce_game_finished":
			_apply_game_finished_event(event)
		"play_cards_to_table":
			_apply_cards_played_event(event)
		"collect_trick_cards":
			_apply_trick_won_event(event)
		"announce_round_finished":
			_apply_round_finished_event(event)
		"highlight_current_turn":
			_apply_turn_highlight_event(event)
	if current_presentation_event_requires_async_ack:
		return
	presentation_bus.acknowledge_current()


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

	_enqueue_presentation_events(snapshot)
	_sync_turn_highlight_state(snapshot)
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
	_refresh_screen_mode()


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
	_refresh_action_feedback(actions)
	_refresh_screen_mode()


func show_error(message: String) -> void:
	error_label.text = message
	push_warning(message)


func _render_cards(container: HBoxContainer, cards: Array) -> void:
	for child in container.get_children():
		child.queue_free()

	if cards.is_empty():
		var empty_label := Label.new()
		empty_label.text = "(empty)"
		empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		empty_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		empty_label.modulate = Color(0.82, 0.85, 0.9, 1)
		container.add_child(empty_label)
		return

	for card_data in cards:
		container.add_child(_build_card_chip(card_data, false))


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
		var is_selected := _contains_card(pending_exchange_cards, card_data) or _contains_card(pending_play_cards, card_data)
		if is_selected:
			card_text = "[%s]" % card_text
		card_button.text = card_text
		card_button.custom_minimum_size = Vector2(90, 54)
		card_button.disabled = not _can_interact_with_hand()
		_apply_card_button_style(card_button, card_data, is_selected)
		card_button.tooltip_text = "Selected" if is_selected else "Click to select"
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
	var team_scores: Array = game_store.state.get("game", {}).get("team_scores", [])
	round_result_label.text = "Round Result: %s\nDelta %s | Total %s\nOut %s" % [
		str(round_result.get("end_reason", "-")),
		str(deltas),
		str(team_scores),
		str(players_out_order),
	]


func _render_players_summary(players: Array) -> void:
	var player_lookup := {}
	var highlighted_player = _current_highlighted_turn_player()
	for player_data in players:
		if typeof(player_data) != TYPE_DICTIONARY:
			continue
		var player_index := int(player_data.get("player_index", -1))
		if player_index < 0 or player_index >= player_panel_containers.size():
			continue
		player_lookup[player_index] = player_data

	for player_index in range(player_panel_containers.size()):
		var player_data: Dictionary = player_lookup.get(player_index, {})
		var is_turn := highlighted_player != null and player_index == int(highlighted_player)
		_render_player_panel(player_index, player_data, is_turn)


func _render_player_panel(player_index: int, player_data: Dictionary, is_turn: bool) -> void:
	var has_player_data := not player_data.is_empty()
	var name_text := "Player %d" % player_index if has_player_data else "Player ?"
	if has_player_data and player_index == game_store.selected_viewer:
		name_text += " (viewer)"
	player_name_labels[player_index].text = name_text
	player_hand_labels[player_index].text = "Hand: %d" % int(player_data.get("hand_count", 0)) if has_player_data else "Hand: -"
	player_status_labels[player_index].text = "Status: %s" % _player_status_text(player_data) if has_player_data else "Status: -"
	player_badge_labels[player_index].text = "Badge: %s" % _player_badge_text(player_data) if has_player_data else "Badge: -"
	player_turn_highlights[player_index].visible = is_turn
	if not has_player_data:
		player_panel_containers[player_index].self_modulate = Color(0.82, 0.82, 0.82, 1)
	elif bool(player_data.get("is_out", false)):
		player_panel_containers[player_index].self_modulate = Color(0.85, 0.9, 0.88, 1)
	elif player_index == game_store.selected_viewer:
		player_panel_containers[player_index].self_modulate = Color(1.0, 0.98, 0.9, 1)
	else:
		player_panel_containers[player_index].self_modulate = Color(1, 1, 1, 1)
	_refresh_player_portrait(player_index)


func _player_status_text(player_data: Dictionary) -> String:
	return "OUT" if player_data.get("is_out", false) else "ACTIVE"


func _player_badge_text(player_data: Dictionary) -> String:
	var badges: Array[String] = []
	if player_data.get("declared_grand_tichu", false):
		badges.append("GRAND")
	if player_data.get("declared_small_tichu", false):
		badges.append("SMALL")
	return "-" if badges.is_empty() else ", ".join(badges)


func set_player_portrait_placeholder(player_index: int) -> void:
	if player_index < 0 or player_index >= player_portrait_labels.size():
		return
	reset_player_portrait_state(player_index)


func set_player_portrait_state(player_index: int, state_name: String, duration_msec: int = 2600) -> void:
	if player_index < 0 or player_index >= portrait_state_by_player.size():
		return
	portrait_state_by_player[player_index] = state_name
	portrait_state_deadline_msec[player_index] = 0 if state_name == "base" else Time.get_ticks_msec() + duration_msec
	_refresh_player_portrait(player_index)


func reset_player_portrait_state(player_index: int) -> void:
	if player_index < 0 or player_index >= portrait_state_by_player.size():
		return
	portrait_state_by_player[player_index] = "base"
	portrait_state_deadline_msec[player_index] = 0
	_refresh_player_portrait(player_index)


func _refresh_player_portrait(player_index: int) -> void:
	var state_name := portrait_state_by_player[player_index]
	var state_title := _portrait_state_title(state_name)
	player_portrait_labels[player_index].text = "P%d\n%s SLOT" % [player_index, state_title]
	player_portrait_labels[player_index].tooltip_text = "Asset slot: player_%d_%s.png" % [player_index, state_name]
	match state_name:
		"declared":
			player_portrait_slots[player_index].self_modulate = Color(1.0, 0.86, 0.55, 1)
			player_portrait_labels[player_index].modulate = Color(0.33, 0.2, 0.0, 1)
		"failed":
			player_portrait_slots[player_index].self_modulate = Color(0.98, 0.62, 0.62, 1)
			player_portrait_labels[player_index].modulate = Color(0.45, 0.05, 0.05, 1)
		_:
			player_portrait_slots[player_index].self_modulate = Color(0.82, 0.9, 1.0, 1)
			player_portrait_labels[player_index].modulate = Color(0.1, 0.2, 0.35, 1)


func _portrait_state_title(state_name: String) -> String:
	match state_name:
		"declared":
			return "Declared"
		"failed":
			return "Failed"
		_:
			return "Base"


func show_declaration_banner(player_index: int, declaration_type: String) -> void:
	declaration_banner_title_label.text = "%s Called" % declaration_type
	declaration_banner_subtitle_label.text = "Player %d commits to the hand." % player_index
	set_player_portrait_state(player_index, "declared", 2600)
	_show_announcement("%s | Player %d" % [declaration_type, player_index], 2600)


func _apply_failed_tichu_portraits(tichu_outcomes: Array) -> void:
	for outcome in tichu_outcomes:
		if typeof(outcome) != TYPE_DICTIONARY:
			continue
		if bool(outcome.get("success", true)):
			continue
		var player_index := int(outcome.get("player_index", -1))
		set_player_portrait_state(player_index, "failed", 3200)


func show_round_result(round_index, totals: Array, deltas: Array) -> void:
	result_overlay.self_modulate = Color(0.87, 0.95, 0.9, 1)
	result_overlay_title_label.text = "Round %s Closed" % str(round_index)
	result_overlay_body_label.text = "Team 0/2: %s (%s)\nTeam 1/3: %s (%s)" % [
		str(_team_score_value(totals, 0)),
		_signed_value_text(_team_score_value(deltas, 0)),
		str(_team_score_value(totals, 1)),
		_signed_value_text(_team_score_value(deltas, 1)),
	]
	_show_score_summary(
		"Round %s | Team 0/2 %s (%s) | Team 1/3 %s (%s)" % [
			str(round_index),
			str(_team_score_value(totals, 0)),
			_signed_value_text(_team_score_value(deltas, 0)),
			str(_team_score_value(totals, 1)),
			_signed_value_text(_team_score_value(deltas, 1)),
		],
		5200
	)


func show_game_result(team_scores: Array) -> void:
	result_overlay.self_modulate = Color(0.93, 0.98, 0.9, 1)
	result_overlay_title_label.text = "Game Finished"
	result_overlay_body_label.text = "Final Score\nTeam 0/2: %s\nTeam 1/3: %s" % [
		str(_team_score_value(team_scores, 0)),
		str(_team_score_value(team_scores, 1)),
	]
	_show_score_summary(
		"Final | Team 0/2 %s | Team 1/3 %s" % [
			str(_team_score_value(team_scores, 0)),
			str(_team_score_value(team_scores, 1)),
		],
		6200
	)


func show_table_cards_refresh() -> void:
	var tween := create_tween()
	table_container.modulate = Color(1, 0.97, 0.82, 0.82)
	table_container.scale = Vector2(0.985, 0.985)
	tween.tween_property(table_container, "modulate", Color(1, 1, 1, 1), 0.18)
	tween.parallel().tween_property(table_container, "scale", Vector2(1.035, 1.035), 0.12)
	tween.tween_property(table_container, "scale", Vector2(1, 1), 0.14)


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


func _build_card_chip(card_data: Variant, compact: bool) -> Control:
	var card_shell := PanelContainer.new()
	card_shell.custom_minimum_size = Vector2(62, 72) if compact else Vector2(76, 100)
	card_shell.self_modulate = _card_background_color(card_data)
	card_shell.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var padding := MarginContainer.new()
	padding.add_theme_constant_override("margin_left", 8)
	padding.add_theme_constant_override("margin_top", 8)
	padding.add_theme_constant_override("margin_right", 8)
	padding.add_theme_constant_override("margin_bottom", 8)
	card_shell.add_child(padding)

	var rows := VBoxContainer.new()
	rows.alignment = BoxContainer.ALIGNMENT_CENTER
	rows.add_theme_constant_override("separation", 4)
	padding.add_child(rows)

	var suit_label := Label.new()
	suit_label.text = _card_suit_badge(card_data)
	suit_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	suit_label.add_theme_color_override("font_color", _card_foreground_color(card_data))
	rows.add_child(suit_label)

	var rank_label := Label.new()
	rank_label.text = _card_rank_text(card_data)
	rank_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rank_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	rank_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rank_label.add_theme_color_override("font_color", _card_foreground_color(card_data))
	rows.add_child(rank_label)

	card_shell.tooltip_text = _format_card(card_data)
	return card_shell


func _apply_card_button_style(card_button: Button, card_data: Variant, is_selected: bool) -> void:
	var background := _card_background_color(card_data)
	if is_selected:
		background = background.lerp(Color(1.0, 0.86, 0.55, 1.0), 0.55)
	card_button.modulate = background
	card_button.add_theme_color_override("font_color", _card_foreground_color(card_data))
	card_button.add_theme_color_override("font_disabled_color", _card_foreground_color(card_data).lerp(Color(0.55, 0.55, 0.55, 1), 0.45))


func _card_background_color(card_data: Variant) -> Color:
	var suit := ""
	if typeof(card_data) == TYPE_DICTIONARY:
		suit = str(card_data.get("suit", "")).to_lower()
	match suit:
		"jade":
			return Color(0.82, 0.95, 0.87, 1)
		"sword":
			return Color(0.86, 0.9, 1.0, 1)
		"pagoda":
			return Color(1.0, 0.89, 0.82, 1)
		"star":
			return Color(0.96, 0.94, 0.78, 1)
		"special":
			return Color(0.9, 0.86, 1.0, 1)
		_:
			return Color(0.91, 0.93, 0.97, 1)


func _card_foreground_color(card_data: Variant) -> Color:
	var suit := ""
	if typeof(card_data) == TYPE_DICTIONARY:
		suit = str(card_data.get("suit", "")).to_lower()
	match suit:
		"jade":
			return Color(0.08, 0.36, 0.22, 1)
		"sword":
			return Color(0.12, 0.26, 0.5, 1)
		"pagoda":
			return Color(0.48, 0.18, 0.08, 1)
		"star":
			return Color(0.45, 0.33, 0.04, 1)
		"special":
			return Color(0.3, 0.14, 0.45, 1)
		_:
			return Color(0.12, 0.18, 0.28, 1)


func _card_suit_badge(card_data: Variant) -> String:
	if typeof(card_data) != TYPE_DICTIONARY:
		return "CARD"
	var suit := str(card_data.get("suit", "")).to_upper()
	return "SP" if suit.is_empty() else suit.left(2)


func _card_rank_text(card_data: Variant) -> String:
	if typeof(card_data) != TYPE_DICTIONARY:
		return str(card_data)
	return str(card_data.get("rank", "?"))


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


func _expire_presentation_state() -> void:
	var now := Time.get_ticks_msec()
	if announcement_deadline_msec > 0 and now >= announcement_deadline_msec:
		announcement_deadline_msec = 0
		announcement_text = ""
		_refresh_announcement_label()
	if table_motion_deadline_msec > 0 and now >= table_motion_deadline_msec:
		table_motion_deadline_msec = 0
		table_motion_text = ""
		_refresh_table_motion_label()
	if score_summary_deadline_msec > 0 and now >= score_summary_deadline_msec:
		score_summary_deadline_msec = 0
		_refresh_score_summary_label()
	for player_index in range(portrait_state_deadline_msec.size()):
		if portrait_state_deadline_msec[player_index] > 0 and now >= portrait_state_deadline_msec[player_index]:
			portrait_state_deadline_msec[player_index] = 0
			reset_player_portrait_state(player_index)


func _clear_presentation_overlays() -> void:
	announcement_text = ""
	table_motion_text = ""
	score_summary_text = ""
	announcement_deadline_msec = 0
	table_motion_deadline_msec = 0
	score_summary_deadline_msec = 0
	for player_index in range(portrait_state_by_player.size()):
		reset_player_portrait_state(player_index)
	_refresh_announcement_label()
	_refresh_table_motion_label()
	_refresh_score_summary_label()


func _show_announcement(text: String, duration_msec: int = 3000) -> void:
	announcement_text = text
	announcement_deadline_msec = Time.get_ticks_msec() + duration_msec
	_refresh_announcement_label()
	_queue_presentation_ack(duration_msec)


func _show_table_motion(text: String, duration_msec: int = 2200) -> void:
	table_motion_text = text
	table_motion_deadline_msec = Time.get_ticks_msec() + duration_msec
	_refresh_table_motion_label()


func _show_score_summary(text: String, duration_msec: int = 5000) -> void:
	score_summary_text = text
	score_summary_deadline_msec = Time.get_ticks_msec() + duration_msec
	_refresh_score_summary_label()
	_queue_presentation_ack(duration_msec)


func _refresh_announcement_label() -> void:
	announcement_label.text = "Announcement: -" if announcement_text.is_empty() else "Announcement: %s" % announcement_text
	declaration_banner.visible = not announcement_text.is_empty()
	if announcement_text.is_empty():
		declaration_banner_title_label.text = "Declaration"
		declaration_banner_subtitle_label.text = ""


func _refresh_table_motion_label() -> void:
	table_motion_label.text = "Table Motion: -" if table_motion_text.is_empty() else "Table Motion: %s" % table_motion_text


func _refresh_score_summary_label() -> void:
	score_summary_label.text = "Round Score: -" if score_summary_text.is_empty() else "Round Score: %s" % score_summary_text
	result_overlay.visible = score_summary_deadline_msec > 0
	if score_summary_deadline_msec == 0:
		result_overlay_title_label.text = "Round Result"
		result_overlay_body_label.text = ""


func _apply_announcement_event(event: Dictionary) -> void:
	var payload: Dictionary = event.get("payload", {})
	var player_index := int(payload.get("player_index", -1))
	var source_effect_type := str(event.get("source_effect_type", ""))
	if source_effect_type == "grand_tichu_declared" and not bool(payload.get("declare", false)):
		return
	var declaration_type := "Grand Tichu" if source_effect_type == "grand_tichu_declared" else "Small Tichu"
	show_declaration_banner(player_index, declaration_type)


func _apply_cards_played_event(event: Dictionary) -> void:
	show_table_cards_refresh()
	_queue_presentation_ack(220)


func _apply_trick_won_event(event: Dictionary) -> void:
	show_table_cards_refresh()
	_queue_presentation_ack(220)


func _apply_round_finished_event(event: Dictionary) -> void:
	var payload: Dictionary = event.get("payload", {})
	var snapshot_context: Dictionary = event.get("snapshot_context", {})
	var deltas: Array = payload.get("score_deltas", [])
	var totals: Array = snapshot_context.get("team_scores", [])
	_apply_failed_tichu_portraits(payload.get("tichu_outcomes", []))
	show_round_result(snapshot_context.get("round_index", "-"), totals, deltas)


func _apply_game_finished_event(event: Dictionary) -> void:
	var payload: Dictionary = event.get("payload", {})
	show_game_result(payload.get("team_scores", []))


func _enqueue_presentation_events(snapshot: Dictionary) -> void:
	var effects: Array = snapshot.get("effects", [])
	if effects.is_empty():
		return
	var events: Array = effect_interpreter.interpret_effects(effects, snapshot)
	if events.is_empty():
		return
	presentation_bus.enqueue_events(events)


func _sync_turn_highlight_state(snapshot: Dictionary) -> void:
	var state: Dictionary = snapshot.get("state", {})
	var table_state: Dictionary = state.get("table", {})
	var phase := str(snapshot.get("phase", ""))
	if phase != "trick" and phase != "await_dragon_recipient":
		presented_turn_highlight_player = null
		return
	if _snapshot_has_effect_type(snapshot, "turn_changed"):
		return
	presented_turn_highlight_player = table_state.get("current_player_index", null)


func _snapshot_has_effect_type(snapshot: Dictionary, effect_type: String) -> bool:
	var effects: Array = snapshot.get("effects", [])
	for effect in effects:
		if typeof(effect) != TYPE_DICTIONARY:
			continue
		if str(effect.get("type", "")) == effect_type:
			return true
	return false


func _apply_turn_highlight_event(event: Dictionary) -> void:
	var payload: Dictionary = event.get("payload", {})
	var snapshot_context: Dictionary = event.get("snapshot_context", {})
	var next_player = payload.get("player_index", snapshot_context.get("current_player_index", null))
	presented_turn_highlight_player = next_player
	_render_players_summary(game_store.state.get("players", []))


func _current_highlighted_turn_player():
	return presented_turn_highlight_player


func _format_cards_inline(cards: Variant) -> String:
	if typeof(cards) != TYPE_ARRAY or cards.is_empty():
		return "-"
	var parts: Array[String] = []
	for card_data in cards:
		if typeof(card_data) == TYPE_DICTIONARY:
			parts.append(_format_card(card_data))
		else:
			parts.append(str(card_data))
	return ", ".join(parts)


func _team_score_value(scores: Variant, index: int):
	if typeof(scores) != TYPE_ARRAY:
		return "-"
	var score_array: Array = scores
	if index < 0 or index >= score_array.size():
		return "-"
	return score_array[index]


func _signed_value_text(value) -> String:
	if typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT:
		return ("%s%s" % ["+" if value >= 0 else "", str(value)])
	return str(value)


func _queue_presentation_ack(duration_msec: int) -> void:
	current_presentation_event_requires_async_ack = true
	var timer := get_tree().create_timer(max(float(duration_msec) / 1000.0, 0.05))
	timer.timeout.connect(_acknowledge_presentation_event_once)


func _acknowledge_presentation_event_once() -> void:
	if not current_presentation_event_requires_async_ack:
		return
	current_presentation_event_requires_async_ack = false
	presentation_bus.acknowledge_current()


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
	render_buttons(game_store.available_actions)


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
	render_buttons(game_store.available_actions)


func _select_option(button: OptionButton, value: int) -> void:
	for item_index in range(button.item_count):
		if button.get_item_id(item_index) == value:
			button.select(item_index)
			return


func _on_viewport_size_changed() -> void:
	_apply_responsive_layout()


func _apply_responsive_layout() -> void:
	var window := get_window()
	var layout_size: Vector2 = window.size if window != null else get_viewport_rect().size
	if layout_size.x <= 0.0 or layout_size.y <= 0.0:
		return

	app_shell.scale = Vector2.ONE
	app_shell.pivot_offset = Vector2.ZERO
	app_shell.position = Vector2.ZERO

	var compact: bool = layout_size.x < 1480.0
	var narrow: bool = layout_size.x < 1320.0
	var very_narrow: bool = layout_size.x < 1120.0

	sidebar_column.custom_minimum_size = Vector2(220 if compact else 320, 0)
	context_column.custom_minimum_size = Vector2(240 if compact else 360, 0)
	players_grid.columns = 1 if narrow else 2
	seat_row.columns = 1 if very_narrow else 2
	control_button_row.columns = 1 if very_narrow else 2
	body_row.add_theme_constant_override("separation", 12 if compact else 18)
	app_shell.add_theme_constant_override("separation", 12 if compact else 16)


func _current_screen_mode() -> String:
	if restoring_session:
		return SCREEN_MODE_RESTORING
	if game_store.has_active_room():
		match game_store.room_status:
			"lobby":
				return SCREEN_MODE_LOBBY
			"in_game":
				return SCREEN_MODE_IN_GAME
			"finished":
				return SCREEN_MODE_FINISHED
	if game_store.has_active_game():
		return SCREEN_MODE_IN_GAME
	return SCREEN_MODE_IDLE


func _refresh_screen_mode() -> void:
	var mode := _current_screen_mode()
	var has_live_board := mode == SCREEN_MODE_IN_GAME or mode == SCREEN_MODE_FINISHED
	match mode:
		SCREEN_MODE_RESTORING:
			screen_hint_label.text = "Mode: restoring saved multiplayer session"
			play_stage_hint_label.text = "Restoring previous room/game..."
			control_hint_label.text = "Direct controls remain visible while multiplayer state restores."
		SCREEN_MODE_LOBBY:
			screen_hint_label.text = "Mode: multiplayer lobby"
			play_stage_hint_label.text = "Lobby is ready. Start the room to move into the play stage."
			control_hint_label.text = "Direct game tools remain available alongside the lobby."
		SCREEN_MODE_IN_GAME:
			screen_hint_label.text = "Mode: live game"
			play_stage_hint_label.text = "Live table is active for Viewer %d / Actor %d." % [
				game_store.selected_viewer,
				game_store.selected_actor,
			]
			control_hint_label.text = "Viewer / Actor switches act as dev inspection controls during live play."
		SCREEN_MODE_FINISHED:
			screen_hint_label.text = "Mode: finished game"
			play_stage_hint_label.text = "Game finished. Review the board, results, or reconnect state."
			control_hint_label.text = "Direct controls remain available for inspection after game end."
		_:
			screen_hint_label.text = "Mode: waiting for room or direct game"
			play_stage_hint_label.text = "Create a room or start a direct dev game to populate the table."
			control_hint_label.text = "Direct game tools stay visible even outside multiplayer."

	lobby_section.modulate = Color(1, 1, 1, 1)
	control_section.modulate = Color(1, 1, 1, 1)
	effects_section.modulate = Color(1, 1, 1, 1) if has_live_board else Color(0.86, 0.86, 0.86, 1)


func _refresh_room_hint() -> void:
	if restoring_session:
		room_hint_label.text = "Restoring saved room session..."
		return
	if not game_store.has_active_room():
		room_hint_label.text = "Create a room or join by code."
		return

	match game_store.room_status:
		"lobby":
			if game_store.my_seat_index < 0:
				room_hint_label.text = "Join an open seat to claim a player slot."
			elif start_room_button.disabled:
				room_hint_label.text = "Waiting for all 4 seats before the host can start."
			else:
				room_hint_label.text = "Host can start the room now."
		"in_game":
			room_hint_label.text = "Room is in game. Use the live table and action context."
		"finished":
			room_hint_label.text = "Room finished. Leave to reset or inspect the latest state."
		_:
			room_hint_label.text = "Room connected."


func _refresh_action_feedback(actions: Dictionary) -> void:
	var live_game_socket: bool = api_client != null and api_client.is_socket_connected_for(game_store.game_id, game_store.selected_viewer)
	var mode := _current_screen_mode()
	var hand_hint := "Select cards when your viewer and actor match."
	var exchange_hint := "Exchange hint: pick 3 cards as viewer=actor."
	var selection_hint := "Selection hint: waiting for playable hand."
	var action_hint := "Action hint: create a room or direct game to start."

	if mode == SCREEN_MODE_RESTORING:
		action_hint = "Action hint: restoring saved session. Wait for room state."
	elif not game_store.has_active_game():
		if game_store.has_active_room():
			action_hint = "Action hint: room is active, but the game has not started yet."
		else:
			action_hint = "Action hint: create a room or direct game to start."
	elif not live_game_socket:
		action_hint = "Action hint: live socket required for Viewer %d." % game_store.selected_viewer
	else:
		if actions.get("can_choose_dragon_recipient", false):
			action_hint = "Action hint: dragon winner must choose an opposing recipient."
		elif game_store.phase == "prepare_exchange":
			action_hint = "Action hint: finish the 3-card exchange."
		elif actions.get("can_declare_grand_tichu", false):
			action_hint = "Action hint: respond to grand tichu before normal play."
		elif actions.get("can_declare_small_tichu", false):
			action_hint = "Action hint: small tichu is available before you play."
		elif actions.get("can_play", false) or actions.get("can_pass", false):
			action_hint = "Action hint: choose cards, then play or pass."
		else:
			action_hint = "Action hint: waiting for the next legal step."

	if not game_store.has_active_game():
		hand_hint = "No live hand yet. Start a room or create a direct game."
	elif game_store.selected_actor != game_store.selected_viewer:
		hand_hint = "Viewer and actor differ. Match them to select cards."
	elif game_store.phase == "prepare_exchange":
		hand_hint = "Choose 3 cards in order: left, teammate, right."
	elif game_store.phase == "trick":
		if actions.get("can_play", false):
			hand_hint = "Select cards to preview the combo before playing."
		else:
			hand_hint = "Hand is visible, but play is not legal for the selected actor."
	else:
		hand_hint = "Hand interactions unlock in exchange or trick phases."

	if not game_store.has_active_game():
		exchange_hint = "Exchange hint: available after the grand tichu step."
	elif game_store.phase != "prepare_exchange":
		exchange_hint = "Exchange hint: inactive outside prepare_exchange."
	elif game_store.selected_actor != game_store.selected_viewer:
		exchange_hint = "Exchange hint: set Viewer and Actor to the same player."
	elif not live_game_socket:
		exchange_hint = "Exchange hint: reconnect the live socket first."
	elif pending_exchange_cards.size() < 3:
		exchange_hint = "Exchange hint: %d of 3 cards selected." % pending_exchange_cards.size()
	else:
		exchange_hint = "Exchange hint: ready to submit."

	var play_helper := _play_selection_helper_text()
	if not game_store.has_active_game():
		selection_hint = "Selection hint: no active game."
	elif game_store.phase != "trick":
		selection_hint = "Selection hint: play selection is active only during trick phase."
	elif game_store.selected_actor != game_store.selected_viewer:
		selection_hint = "Selection hint: set Viewer and Actor to the same player."
	elif not live_game_socket:
		selection_hint = "Selection hint: reconnect the live socket first."
	elif pending_play_cards.is_empty():
		selection_hint = "Selection hint: choose at least one card."
	else:
		if not play_helper.is_empty():
			selection_hint = "Selection hint: %s" % play_helper
		else:
			selection_hint = "Selection hint: combo selected."

	action_hint_label.text = action_hint
	hand_hint_label.text = hand_hint
	exchange_hint_label.text = exchange_hint
	selection_hint_label.text = selection_hint


func _update_status_label() -> void:
	status_label.text = "%s | %s" % [http_status_message, socket_status_message]
	_refresh_screen_mode()


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
		_refresh_screen_mode()
		_refresh_action_feedback({})


func _resume_room_or_game_socket() -> void:
	if not game_store.has_active_room():
		_refresh_screen_mode()
		return
	if game_store.room_status == "lobby":
		api_client.connect_room_socket(game_store.room_code, game_store.seat_token)
		_refresh_screen_mode()
		_refresh_action_feedback({})
		return

	if game_store.room_status == "in_game" or game_store.room_status == "finished":
		api_client.connect_game_socket(game_store.game_id, game_store.selected_viewer, game_store.seat_token)
		api_client.get_snapshot(game_store.game_id, game_store.selected_viewer, game_store.seat_token)
		_refresh_screen_mode()


func _update_room_ui() -> void:
	if not game_store.has_active_room():
		room_status_label.text = "Room: -"
		create_room_button.disabled = false
		start_room_button.disabled = true
		leave_room_button.disabled = true
		for seat_index in range(seat_buttons.size()):
			seat_buttons[seat_index].text = "Seat %d" % seat_index
			seat_buttons[seat_index].disabled = false
		_refresh_room_hint()
		return

	var snapshot: Dictionary = game_store.room_snapshot
	var seats: Array = snapshot.get("seats", [])
	room_status_label.text = "Room %s | Status %s | Seat %d" % [
		game_store.room_code,
		game_store.room_status,
		game_store.my_seat_index,
	]
	create_room_button.disabled = true
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
	_refresh_room_hint()
	_refresh_screen_mode()


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
	_refresh_screen_mode()
	_refresh_room_hint()
	_refresh_action_feedback({})
	api_client.get_room_state(room_code, seat_token)


func _clear_room_runtime() -> void:
	restoring_session = false
	game_store.clear_multiplayer_identity()
	presentation_bus.clear()
	presented_turn_highlight_player = null
	_clear_presentation_overlays()
	room_code_input.text = ""
	recent_effect_lines.clear()
	_render_effects()
	phase_label.text = "Phase: -"
	turn_label.text = "Turn: -"
	game_info_label.text = "Scores: - | Round: -"
	_render_hand_cards([])
	_render_cards(table_container, [])
	_render_round_result({})
	_render_players_summary([])
	_render_players_out_order([])
	_render_dragon_recipient_options({})
	_update_room_ui()
	_refresh_action_feedback({})
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
	if pending_play_cards.is_empty():
		selected_play_label.text = "Selected: -"
		return

	var texts: Array[String] = []
	for card_data in pending_play_cards:
		texts.append(_format_card(card_data))
	selected_play_label.text = "Selected: %s" % ", ".join(texts)


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
