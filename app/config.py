class Config:
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///database.db"
    

    PFP_FOLDER = "app/static/profile-pics"
    BG_FOLDER = "app/static/bg-pics"
    BANNER_FOLDER = "app/static/banner-pics"
    WALK_IN_FOLDER = "app/static/walk-ins"
    POST_FOLDER = "app/static/post-content"
    ALLOWED_IMG_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "jfif"}
    ALLOWED_AUDIO_EXTENSIONS = {"mp3"}
    HEX_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    DEFAULTPIC = "/static/profile-pics/default.png"
    DEFAULTPIC_INVERTED = "/static/profile-pics/default-inverted.png"
    ALLOWED_TAGS = {"b", "i", "u", "ul", "ol", "li"}
    MAX_PROFILE_COMMENTS = 5
    DEFAULT_PRIMARY_COLOR = "#3985f8"
    SEARCH_LOGO_PRIMARY_LIGHT = "VibeGrid-Search-light.png"
    SEARCH_LOGO_PRIMARY_DARK = "VibeGrid-Search-dark.png"
    SEARCH_LOGO_BW_LIGHT = "VibeGrid-Search-bw-light.png"
    SEARCH_LOGO_BW_DARK = "VibeGrid-Search-bw-dark.png"