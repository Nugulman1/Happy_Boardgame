extends Node

signal presentation_event_started(event: Dictionary)
signal queue_changed(pending_count: int, is_processing: bool)

var _queue: Array = []
var _current_event: Dictionary = {}
var _is_processing := false


func enqueue_events(events: Array) -> void:
	for event in events:
		if typeof(event) != TYPE_DICTIONARY:
			continue
		_queue.append(event.duplicate(true))
	_emit_queue_changed()
	_try_dispatch_next()


func clear() -> void:
	_queue.clear()
	_current_event.clear()
	_is_processing = false
	_emit_queue_changed()


func acknowledge_current() -> void:
	if not _is_processing:
		return
	_current_event.clear()
	_is_processing = false
	_emit_queue_changed()
	call_deferred("_try_dispatch_next")


func pending_count() -> int:
	return _queue.size() + (1 if _is_processing else 0)


func is_dispatching() -> bool:
	return _is_processing


func _try_dispatch_next() -> void:
	if _is_processing or _queue.is_empty():
		_emit_queue_changed()
		return

	_current_event = _queue[0]
	_queue.remove_at(0)
	_is_processing = true
	_emit_queue_changed()
	presentation_event_started.emit(_current_event.duplicate(true))


func _emit_queue_changed() -> void:
	queue_changed.emit(pending_count(), _is_processing)
