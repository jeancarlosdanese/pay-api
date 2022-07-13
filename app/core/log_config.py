from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    """
    ## Possible field variables
    %(name)s            Name of the logger (logging channel)
    %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
                        WARNING, ERROR, CRITICAL)
    %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
                        "WARNING", "ERROR", "CRITICAL")
    %(pathname)s        Full pathname of the source file where the logging
                        call was issued (if available)
    %(filename)s        Filename portion of pathname
    %(module)s          Module (name portion of filename)
    %(lineno)d          Source line number where the logging call was issued
                        (if available)
    %(funcName)s        Function name
    %(created)f         Time when the LogRecord was created (time.time()
                        return value)
    %(asctime)s         Textual time when the LogRecord was created
    %(msecs)d           Millisecond portion of the creation time
    %(relativeCreated)d Time in milliseconds when the LogRecord was created,
                        relative to the time the logging module was loaded
                        (typically at application startup time)
    %(thread)d          Thread ID (if available)
    %(threadName)s      Thread name (if available)
    %(process)d         Process ID (if available)
    %(message)s         The result of record.getMessage(), computed just as
                        the record is emitted
    """

    LOGGER_NAME: str = "app"
    LOG_FORMAT: str = "%(levelprefix)s %(asctime)s ⟨%(module)s::%(funcName)s ➜ %(lineno)d⟩ : %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": LOG_FORMAT,
        },
        "verbose": {
            "format": "%(asctime)s - %(levelname)s: %(module)s %(process)d %(thread)d %(message)s",
        },
        "simple": {
            "format": "%(asctime)s - %(levelname)s: - %(name)s - %(message)s",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        # "console": {
        #     "level": "DEBUG",
        #     "class": "logging.StreamHandler",
        #     "formatter": "default",
        #     "stream": "ext://sys.stdout",
        # },
        # "info_file_handler": {
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "level": "INFO",
        #     "formatter": "default",
        #     "filename": "info.log",
        #     "maxBytes": 10485760,
        #     "backupCount": 40,
        #     "encoding": "utf8",
        # },
        # "error_file_handler": {
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "level": "ERROR",
        #     "formatter": "default",
        #     "filename": "errors.log",
        #     "maxBytes": 10485760,
        #     "backupCount": 40,
        #     "encoding": "utf8",
        # },
    }
    loggers = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }
