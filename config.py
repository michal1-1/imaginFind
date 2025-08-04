TEMP_IMAGE_DIR = "temp_images"
# IMAGE_DB_DIR = "images_db"
IMAGE_DB_DIR = r"D:\coco\val2017"
TOP_K = 10
SCORE_THRESHOLD = 0.5
MAX_RESULTS = 5
NUM_CLUSTERS_COCO = 5
RANDOM_STATE = 42
TOP_N_KEYWORDS = 5
TFIDF_MAX_FEATURES = 100
DEFAULT_NUM_CLUSTERS = 5
TTL = 300
MAXSIZE = 100
THRESHOLD = 1
ROUND_DECIMALS = 4
ROUND=2
STATUS_CODE_SERVER = 500
BUG_REQEST = 400
TOP_K = 10
MIN_K=2
TIME_SLEEP = 0.2
SCORE = 2
EXTRA_TRAINING_DIR = "D:/extra_training_data"
MAX_NEW_TOKENS = 30
MIN_WORD_LENGTH = 3
MAX_CLUSTERS_PER_CATEGORY = 5
MIN_CLUSTERS_PER_CATEGORY = 2
CLUSTERING_DIVISOR = 10
COHERENCE_SCALE = 2
MAX_CLUSTERS_PER_CATEGORY=8
CLUSTERING_DIVISOR=3
CONFIDENCE_SCALING_FACTOR=10
MAX_CONFIDENCE_SCORE=85.0
TOP_CLUSTER_KEYWORDS = 5
ROUND_CLUSTER_CONFIDENCE = 1
MIN_IMAGES_FOR_CLUSTERING = 2
CLUSTER_LOG_PRINT_INTERVAL = 100
MIN_CLUSTER_KEYWORD_LENGTH = 2
KMEANS_N_INIT = 10
CLUSTERING_MIN_CLUSTERS = 1
COMMIT_INTERVAL = 5
DEFAULT_NUM_CLUSTERS = 5
DEFAULT_MAX_K = 8
DEFAULT_MIN_K = 2
KMEANS_RANDOM_STATES = [42, 123, 456, 789]
KMEANS_N_INIT = 10
KMEANS_MAX_ITER = 300
KMEANS_TOL = 1e-4
DBSCAN_K_NEIGHBORS = 5
KMEANS_N_INIT_EXPLORATION = 5
DBSCAN_EPS_PERCENTILE = 75
DBSCAN_MIN_SAMPLES_DIVISOR = 25
MIN_VALID_EMBEDDING_STD = 1e-6
MIN_CLUSTER_SIZE = 2
DEFAULT_CLUSTER_ID = 0
BALANCE_SCORE_BASE = 1.0
CLUSTERING_MIN_CLUSTERS = 1
KMEANS_MAX_K_LIMIT = 8
KMEANS_MAX_ITER_EXPLORATION = 100
DEFAULT_CLUSTER_SCORE = 0.0
MIN_SAMPLES_FOR_DBSCAN = 10
DBSCAN_NOISE_LABEL = -1
EMBEDDING_CLIP_PERCENTILE = 99
DBSCAN_MIN_SAMPLES_MIN = 2
DBSCAN_MAX_CLUSTER_RATIO = 0.5
TEST_SIZE = 0.2

CLUSTER_CATEGORIES = [
    "animals", "people", "buildings", "nature", "food",
    "vehicles", "technology", "sports", "indoor", "outdoor",
    "landscape", "furniture", "clothes", "toys", "documents",
    "instruments", "art", "transportation", "pets", "plants",
    "bathroom", "kitchen", "office", "electronics", "sky",
    "water", "celebration", "market", "street", "child",
    "drinks", "interior", "workspace"
]

keyword_to_category = {
    # Animals
    "cat": "animals", "dog": "animals", "horse": "animals", "cow": "animals", "bird": "animals",
    "elephant": "animals", "sheep": "animals", "giraffe": "animals", "zebra": "animals",
    "bear": "animals", "monkey": "animals", "rabbit": "animals", "lion": "animals", "duck": "animals",
    "fish": "animals", "goat": "animals", "chicken": "animals", "fox": "animals",

    # Furniture
    "chair": "furniture", "table": "furniture", "couch": "furniture", "sofa": "furniture",
    "bed": "furniture", "bench": "furniture", "cabinet": "furniture",
    "drawer": "furniture", "shelf": "furniture", "bookshelf": "furniture", "dresser": "furniture",

    # Bathroom
    "toilet": "bathroom", "sink": "bathroom", "bathtub": "bathroom", "shower": "bathroom", "towel": "bathroom",

    # Kitchen
    "fridge": "kitchen", "microwave": "kitchen", "oven": "kitchen", "stove": "kitchen", "kettle": "kitchen",
    "blender": "kitchen", "toaster": "kitchen", "pan": "kitchen", "pot": "kitchen", "dish": "kitchen",

    # Office
    "laptop": "office", "computer": "office", "keyboard": "office", "mouse": "office",
    "printer": "office", "notebook": "office", "pen": "office",

    # Vehicles / transportation
    "car": "vehicles", "bus": "vehicles", "train": "vehicles", "truck": "vehicles",
    "motorcycle": "vehicles", "bike": "vehicles", "airplane": "vehicles", "boat": "vehicles",

    # Food
    "pizza": "food", "cake": "food", "sandwich": "food", "apple": "food", "banana": "food",
    "orange": "food", "burger": "food", "salad": "food", "ice cream": "food", "bread": "food",

    # Nature & plants
    "tree": "plants", "plant": "plants", "flower": "plants", "leaf": "plants", "grass": "plants",
    "mountain": "nature", "river": "water", "lake": "water", "sea": "water", "cloud": "sky", "sky": "sky",
    "beach": "nature", "forest": "nature",

    # Clothing
    "shirt": "clothes", "pants": "clothes", "dress": "clothes", "jacket": "clothes",
    "shoes": "clothes", "hat": "clothes", "skirt": "clothes", "suit": "clothes",

    # Toys
    "teddy": "toys", "ball": "toys", "lego": "toys", "doll": "toys", "game": "toys",

    # People
    "man": "people", "woman": "people", "child": "child", "boy": "child", "girl": "child",

    # Celebration
    "balloon": "celebration", "cake": "celebration", "birthday": "celebration", "fireworks": "celebration",
    "party": "celebration",

    # Tech
    "phone": "electronics", "tablet": "electronics", "tv": "electronics", "camera": "electronics",

    # Music
    "guitar": "instruments", "piano": "instruments", "violin": "instruments", "drum": "instruments",

    # Art
    "painting": "art", "sculpture": "art", "drawing": "art", "statue": "art",

    # Misc
    "building": "buildings", "market": "market", "street": "street", "document": "documents", "paper": "documents",

    # משקאות - Drinks
    "glass of": "drinks",
    "cup of": "drinks",
    "coffee": "drinks",
    "tea": "drinks",
    "drink": "drinks",
    "beverage": "drinks",
    "bottle": "drinks",
    "mug": "drinks",

    # עיצוב פנים - Interior
    "room": "interior",
    "bedroom": "interior",
    "living room": "interior",
    "closet": "interior",
    "wardrobe": "interior",
    "interior": "interior",
    "hanging clothes": "interior",

    # סביבת עבודה - Workspace
    "desk": "workspace",
    "computer setup": "workspace",
    "home office": "workspace",
    "workstation": "workspace",
    "office desk": "workspace",
    "monitor": "workspace"
}

category_keywords = {
    "Animals": ["cat", "dog", "horse", "cow", "bird", "elephant", "sheep", "animal",
                "pet", "zoo", "farm", "wildlife", "kitten", "puppy"],
    "People": ["man", "woman", "person", "boy", "girl", "child", "baby", "people",
               "human", "family", "group", "crowd"],
    "Food": ["food", "meal", "eating", "cake", "pizza", "sandwich", "fruit", "vegetable",
             "dinner", "lunch", "breakfast", "cooking", "kitchen", "restaurant"],
    "Vehicles": ["car", "bus", "train", "truck", "motorcycle", "bike", "airplane",
                 "boat", "vehicle", "driving", "transportation"],
    "Nature": ["tree", "flower", "garden", "forest", "mountain", "beach", "ocean",
               "sky", "sunset", "landscape", "outdoor", "park"],
    "Buildings": ["building", "house", "church", "bridge", "architecture", "city",
                  "street", "road", "construction"],
    "Sports": ["tennis", "baseball", "football", "basketball", "soccer", "sport",
               "game", "playing", "ball", "field"],
    "Electronics": ["computer", "phone", "television", "laptop", "screen", "device",
                    "electronic", "technology"],
    "Furniture": ["chair", "table", "bed", "sofa", "furniture", "room", "living",
                  "bedroom", "sitting"],
    "Clothes": ["shirt", "dress", "hat", "shoes", "clothing", "wearing", "fashion"]
}
CATEGORIES = ["animals", "people", "food", "vehicles", "nature", "sports", "furniture", "electronics", "indoor",
              "outdoor", "toys"]
CLUSTER_CONFIDENCE_THRESHOLD = 40.0