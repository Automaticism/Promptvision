import torch
import clip
from pathlib import Path
from PIL import Image

STATE_NAME = "static/models/sac+logos+ava1-l14-linearMSE.pth"
MODEL_DIM = 768

class AestheticPredictor(torch.nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.input_size = input_size
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(self.input_size, 1024),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(1024, 128),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(128, 64),
            torch.nn.Dropout(0.1),
            torch.nn.Linear(64, 16),
            torch.nn.Linear(16, 1)
        )

    def forward(self, x):
        return self.layers(x)

def load_predictor(state_name, device):
    pt_state = torch.load(state_name, map_location=torch.device(device))
    predictor = AestheticPredictor(MODEL_DIM)
    predictor.load_state_dict(pt_state)
    predictor.to(device)
    predictor.eval()
    return predictor

def get_image_features(image, device, model, preprocess):
    image = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image)
        # l2 normalize
        image_features /= image_features.norm(dim=-1, keepdim=True)
    image_features = image_features.cpu().detach().numpy()
    return image_features

def get_score(image, predictor, device, model, preprocess):
    image_features = get_image_features(image, device, model, preprocess)
    score = predictor(torch.from_numpy(image_features).to(device).float())
    return round(score.item(), 2)

class aesthetic_engine():
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device detected in aesthetic engine: {self.device}")
        self.predictor = load_predictor(STATE_NAME, self.device)
        self.clip_model, self.clip_preprocess = clip.load("ViT-L/14", device=self.device)

    def score(self, image_path):
        img = Image.open(image_path)
        return get_score(img, self.predictor, self.device, self.clip_model, self.clip_preprocess)