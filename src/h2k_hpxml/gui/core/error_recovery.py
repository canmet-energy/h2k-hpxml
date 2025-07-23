"""
Error Recovery and Notification System

Provides robust error handling, recovery mechanisms, and user notifications.
Features:
- Automatic retry with exponential backoff
- Error categorization and recovery strategies
- User notification system with toast messages
- Error logging and reporting
"""

import time
import threading
import traceback
from typing import Dict, List, Callable, Optional, Any
from pathlib import Path
import logging


class ErrorRecoveryManager:
    """Manages error recovery and user notifications."""
    
    def __init__(self):
        self.retry_strategies = {}
        self.notification_callbacks = []
        self.error_log = []
        
        # Configure logging
        self.logger = logging.getLogger('h2k_gui_errors')
        self.logger.setLevel(logging.ERROR)
        
        # Default retry strategies
        self.register_default_strategies()
        
    def register_default_strategies(self):
        """Register default error recovery strategies."""
        
        # File system errors
        self.register_strategy(
            'file_not_found',
            max_retries=3,
            delay=1.0,
            recovery_action=self._retry_file_operation
        )
        
        # Network/dependency errors
        self.register_strategy(
            'dependency_error',
            max_retries=2,
            delay=2.0,
            recovery_action=self._retry_dependency_check
        )
        
        # Conversion errors
        self.register_strategy(
            'conversion_error',
            max_retries=1,
            delay=0.5,
            recovery_action=self._retry_conversion
        )
        
        # Memory errors
        self.register_strategy(
            'memory_error',
            max_retries=2,
            delay=5.0,
            recovery_action=self._cleanup_memory
        )
        
    def register_strategy(self, error_type: str, max_retries: int, delay: float, 
                         recovery_action: Optional[Callable] = None):
        """Register an error recovery strategy."""
        self.retry_strategies[error_type] = {
            'max_retries': max_retries,
            'base_delay': delay,
            'recovery_action': recovery_action
        }
        
    def add_notification_callback(self, callback: Callable):
        """Add a callback for error notifications."""
        self.notification_callbacks.append(callback)
        
    def handle_error(self, error: Exception, error_type: str, context: Dict[str, Any] = None) -> bool:
        """Handle an error with appropriate recovery strategy."""
        error_info = {
            'error': error,
            'error_type': error_type,
            'context': context or {},
            'timestamp': time.time(),
            'traceback': traceback.format_exc()
        }
        
        self.error_log.append(error_info)
        self.logger.error(f"{error_type}: {str(error)}", exc_info=True)
        
        # Try to recover
        if error_type in self.retry_strategies:
            return self._attempt_recovery(error_info)
        else:
            # No recovery strategy, notify user
            self._notify_error(error_info, recoverable=False)
            return False
            
    def _attempt_recovery(self, error_info: Dict[str, Any]) -> bool:
        """Attempt to recover from an error."""
        error_type = error_info['error_type']
        strategy = self.retry_strategies[error_type]
        
        max_retries = strategy['max_retries']
        base_delay = strategy['base_delay']
        recovery_action = strategy['recovery_action']
        
        for attempt in range(max_retries):
            try:
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                
                # Try recovery action if available
                if recovery_action:
                    recovery_action(error_info, attempt + 1)
                    
                # Notify user of recovery attempt
                self._notify_recovery_attempt(error_info, attempt + 1, max_retries)
                
                # If we get here, recovery succeeded
                self._notify_recovery_success(error_info, attempt + 1)
                return True
                
            except Exception as e:
                # Recovery failed, try again or give up
                if attempt == max_retries - 1:
                    # Final attempt failed
                    error_info['recovery_error'] = str(e)
                    self._notify_recovery_failed(error_info, max_retries)
                    return False
                    
        return False
        
    def _retry_file_operation(self, error_info: Dict[str, Any], attempt: int):
        """Recovery action for file operation errors."""
        context = error_info['context']
        
        # Check if file exists now
        file_path = context.get('file_path')
        if file_path and Path(file_path).exists():
            return  # File is available now
            
        # Try to create parent directories
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
        raise Exception("File still not available")
        
    def _retry_dependency_check(self, error_info: Dict[str, Any], attempt: int):
        """Recovery action for dependency errors."""
        # This could trigger dependency installation
        context = error_info['context']
        
        # Check if dependencies are available now
        try:
            import openstudio
            if Path("/OpenStudio-HPXML/").exists():
                return  # Dependencies are available
        except ImportError:
            pass
            
        raise Exception("Dependencies still not available")
        
    def _retry_conversion(self, error_info: Dict[str, Any], attempt: int):
        """Recovery action for conversion errors."""
        # This could try with different conversion options
        context = error_info['context']
        
        # Try with simpler options
        if 'options' in context:
            options = context['options'].copy()
            options['skip_validation'] = True
            options['debug_mode'] = False
            context['simplified_options'] = options
            
        raise Exception("Retry conversion with simplified options")
        
    def _cleanup_memory(self, error_info: Dict[str, Any], attempt: int):
        """Recovery action for memory errors."""
        import gc
        gc.collect()
        
        # Could also reduce batch size or clear caches
        time.sleep(2)  # Give system time to free memory
        
    def _notify_error(self, error_info: Dict[str, Any], recoverable: bool = True):
        """Notify user of an error."""
        notification = {
            'type': 'error',
            'title': 'Error Occurred',
            'message': str(error_info['error']),
            'error_type': error_info['error_type'],
            'recoverable': recoverable,
            'timestamp': error_info['timestamp']
        }
        
        self._send_notification(notification)
        
    def _notify_recovery_attempt(self, error_info: Dict[str, Any], attempt: int, max_attempts: int):
        """Notify user of recovery attempt."""
        notification = {
            'type': 'info',
            'title': 'Attempting Recovery',
            'message': f"Trying to recover from {error_info['error_type']} (attempt {attempt}/{max_attempts})",
            'auto_hide': True,
            'timestamp': time.time()
        }
        
        self._send_notification(notification)
        
    def _notify_recovery_success(self, error_info: Dict[str, Any], attempts: int):
        """Notify user of successful recovery."""
        notification = {
            'type': 'success',
            'title': 'Recovery Successful',
            'message': f"Recovered from {error_info['error_type']} after {attempts} attempt(s)",
            'auto_hide': True,
            'timestamp': time.time()
        }
        
        self._send_notification(notification)
        
    def _notify_recovery_failed(self, error_info: Dict[str, Any], attempts: int):
        """Notify user of failed recovery."""
        notification = {
            'type': 'error',
            'title': 'Recovery Failed',
            'message': f"Could not recover from {error_info['error_type']} after {attempts} attempts",
            'recoverable': False,
            'timestamp': time.time()
        }
        
        self._send_notification(notification)
        
    def _send_notification(self, notification: Dict[str, Any]):
        """Send notification to all registered callbacks."""
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                self.logger.error(f"Notification callback failed: {e}")
                
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get the error log."""
        return self.error_log.copy()
        
    def clear_error_log(self):
        """Clear the error log."""
        self.error_log.clear()
        
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error statistics."""
        stats = {}
        for error_info in self.error_log:
            error_type = error_info['error_type']
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats


class NotificationSystem:
    """Handles user notifications and toast messages."""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.active_notifications = []
        self.notification_queue = []
        
    def show_notification(self, notification: Dict[str, Any]):
        """Show a notification to the user."""
        # Create notification widget
        import customtkinter as ctk
        
        notification_frame = ctk.CTkFrame(self.parent)
        notification_frame.pack(side="top", fill="x", padx=10, pady=2)
        
        # Color based on type
        colors = {
            'error': ('red', 'white'),
            'warning': ('orange', 'white'),
            'info': ('blue', 'white'),
            'success': ('green', 'white')
        }
        
        bg_color, text_color = colors.get(notification['type'], ('gray', 'white'))
        
        # Notification content
        content_frame = ctk.CTkFrame(notification_frame, fg_color=bg_color)
        content_frame.pack(fill="x", padx=2, pady=2)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=notification['title'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=text_color
        )
        title_label.pack(anchor="w", padx=10, pady=(5, 2))
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=notification['message'],
            font=ctk.CTkFont(size=11),
            text_color=text_color,
            wraplength=400
        )
        message_label.pack(anchor="w", padx=10, pady=(2, 5))
        
        # Close button
        close_btn = ctk.CTkButton(
            content_frame,
            text="×",
            width=20,
            height=20,
            command=lambda: self._close_notification(notification_frame)
        )
        close_btn.pack(side="right", padx=5, pady=5)
        
        self.active_notifications.append(notification_frame)
        
        # Auto-hide if requested
        if notification.get('auto_hide', False):
            self.parent.after(5000, lambda: self._close_notification(notification_frame))
            
    def _close_notification(self, notification_frame):
        """Close a notification."""
        if notification_frame in self.active_notifications:
            self.active_notifications.remove(notification_frame)
            notification_frame.destroy()
            
    def clear_all_notifications(self):
        """Clear all active notifications."""
        for notification_frame in self.active_notifications:
            notification_frame.destroy()
        self.active_notifications.clear()