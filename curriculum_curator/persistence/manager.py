import json
import yaml
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger()


class PersistenceManager:
    """Manages data persistence for curriculum curator."""
    
    def __init__(self, config):
        """Initialize the persistence manager.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.base_dir = Path(config.get("system", {}).get("persistence_dir", ".curriculum_curator"))
        self.sessions_dir = self.base_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("persistence_manager_initialized", 
                   base_dir=str(self.base_dir),
                   sessions_dir=str(self.sessions_dir))
    
    def create_session(self, session_id=None):
        """Create a new session directory and return the session ID.
        
        Args:
            session_id (str, optional): Specific session ID to use
            
        Returns:
            tuple: (session_id, session_dir)
        """
        if session_id is None:
            from datetime import datetime
            import uuid
            session_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        logger.info("session_created", session_id=session_id, session_dir=str(session_dir))
        return session_id, session_dir
    
    def save_session_state(self, session_id, context):
        """Save the current session state to disk.
        
        Args:
            session_id (str): Session ID
            context (dict): Session context to save
        """
        session_dir = self.sessions_dir / session_id
        
        # Save context (excluding large content)
        sanitized_context = {
            k: v for k, v in context.items() 
            if isinstance(v, (str, int, float, bool, list, dict))
            and not isinstance(v, str) or len(v) < 10000
        }
        
        with open(session_dir / "context.json", "w") as f:
            json.dump(sanitized_context, f, default=str, indent=2)
            
        logger.debug("session_state_saved", session_id=session_id)
    
    def save_config(self, session_id, config):
        """Save the configuration used for this session.
        
        Args:
            session_id (str): Session ID
            config (dict): Configuration to save
        """
        session_dir = self.sessions_dir / session_id
        
        with open(session_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
            
        logger.debug("session_config_saved", session_id=session_id)
    
    def append_prompt_history(self, session_id, request):
        """Append a prompt request to the prompt history.
        
        Args:
            session_id (str): Session ID
            request (LLMRequest): Request to append to history
        """
        session_dir = self.sessions_dir / session_id
        
        with open(session_dir / "prompt_history.jsonl", "a") as f:
            json_record = {
                "timestamp": request.timestamp.isoformat(),
                "provider": request.provider,
                "model": request.model,
                "step_name": request.step_name,
                "status": request.status,
                "input_tokens": request.input_tokens,
                "output_tokens": request.output_tokens,
                "cost": request.cost,
                "duration": request.duration,
                "prompt": request.prompt[:1000] + "..." if len(request.prompt) > 1000 else request.prompt,
            }
            f.write(json.dumps(json_record) + "\n")
            
        logger.debug("prompt_history_appended", 
                    session_id=session_id, 
                    provider=request.provider,
                    model=request.model)
    
    def save_usage_report(self, session_id, usage_report):
        """Save the usage report for this session.
        
        Args:
            session_id (str): Session ID
            usage_report (dict): Usage report to save
        """
        session_dir = self.sessions_dir / session_id
        
        with open(session_dir / "usage_report.json", "w") as f:
            json.dump(usage_report, f, default=str, indent=2)
            
        logger.debug("usage_report_saved", session_id=session_id)
    
    def load_session(self, session_id):
        """Load a session state from disk.
        
        Args:
            session_id (str): Session ID to load
            
        Returns:
            dict: Session data or None if not found
        """
        session_dir = self.sessions_dir / session_id
        
        if not session_dir.exists():
            logger.warning("session_not_found", session_id=session_id)
            return None
        
        # Load context
        context = {}
        context_file = session_dir / "context.json"
        if context_file.exists():
            with open(context_file, "r") as f:
                context = json.load(f)
        
        # Load config
        config = None
        config_file = session_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
        
        logger.info("session_loaded", session_id=session_id)
        return {
            "session_id": session_id,
            "context": context,
            "config": config
        }
    
    def list_sessions(self):
        """List all available sessions.
        
        Returns:
            list: List of session IDs
        """
        sessions = [d.name for d in self.sessions_dir.iterdir() if d.is_dir()]
        logger.info("sessions_listed", count=len(sessions))
        return sessions