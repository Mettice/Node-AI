@echo off
echo Rendering Remotion video: %1
npx remotion render %1 --codec=h264 --crf=18 --pixel-format=yuv420p --output=output/%1.mp4
echo Done! Video saved to output/%1.mp4
