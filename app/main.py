import sys
from app.pipeline import run_pipeline


def load_emotions(path="emotions.txt"):
    with open(path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def main():
    mode = "all"

    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if mode not in ["image", "luma", "all"]:
        raise ValueError("Mode must be: image, luma, or all")

    emotions = load_emotions()

    for index, emotion in enumerate(emotions, start=1):
        print("=" * 60)
        print(f"Emotion: {emotion}")
        print(f"Mode: {mode}")

        run_pipeline(emotion, index, mode=mode)


if __name__ == "__main__":
    main()
