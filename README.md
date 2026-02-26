# Subtitle Generator

This Desktop App generates the subtitle for any video you input, into both SRT (option to burn-in as well) and ASS format. 
In ASS format, you can edit the overall appearance of the subtitles with a preview as well.
Uses Whisper for speech-recognition and ffmpeg for video conversion and text burning

## How to install
1. pip install -r requirements.txt
2. Make sure to install compatible cuda and pytorch versions for using GPU with Whisper
3. Run main.py


## Usage

### Step 1 : Run main.py
Launches the UI window, which should look as follows:
<img width="1920" height="1080" alt="Screenshot 2026-02-25 11-59-35" src="https://github.com/user-attachments/assets/83d6a181-6950-4d1a-9611-7b6422c96218" />


### Step 2 : Select video
Click on Select video, and choose the video you which to add subtitles to. Once added, a single frame of the video should appear as follows:
<img width="1920" height="1080" alt="Screenshot 2026-02-25 12-03-01" src="https://github.com/user-attachments/assets/ac1a8875-beaf-4a0c-9e49-9fee4e5c29b2" />


### Step 3 : Adjust subtitle parameters
Adjust the parameters before generating subs. Segment refers the group of words that appear together at the same time.

-- Max words per line = Number of words to appear in one line, within a segment. If words in a segment exceed this, the segment is split into multiple lines, each having words within this limit
-- Max segment duration(s) = How long in duration should one segment be, in seconds. For example, if set as 5 seconds, the segments will only consist of words spoken in 5 second intervals
-- Max words per segment = Number of words in a segment. All segments will have at most this many number of words

This options can be combined and are independent, since they are upper bounds

-- Processing device = choose between cuda, mps and cpu for the Whisper model to run on.
-- Whisper model size = The model size for the speech-recognition model. Use small if you have an average GPU, gives decent enough results

<img width="1192" height="701" alt="Screenshot 2026-02-25 120824" src="https://github.com/user-attachments/assets/88d116d7-4ae3-435b-9fef-d4a1e4cf7875" />
<img width="1192" height="701" alt="Screenshot 2026-02-25 120849" src="https://github.com/user-attachments/assets/fec48a0a-d1d2-491b-bc1f-5bf2c065748d" />

### Step 4 : Generate Subtitles (SRT)
Click on Generate Subtitles, this will load the Whisper model and generate subtitles in SRT format. The output will be populated in the scrollable section below
<img width="1920" height="1032" alt="Screenshot 2026-02-25 121038" src="https://github.com/user-attachments/assets/6b24f5f3-2097-450e-94c9-97d80d94f368" />

You can edit here as you wish. Once edited as per requirements, proceed to next step. If you wish to create ASS subtitles only, skip to step 6 

### Step 5 : Create SRT and Burn-in to video
Tick the checkbox 'Burn in Subtitles' if you wish to burn the subtitles into the video itself and have a separate SRT file as well. Otherwise, only the SRT file will be generated.
Click on 'Save SRT and Convert to Video' to do so.

<img width="1920" height="1032" alt="Screenshot 2026-02-25 121512" src="https://github.com/user-attachments/assets/964d4650-a80e-4128-b132-47dcb592287e" />


### Step 6 : Convert to ASS formata
Click on 'convert to ASS' to generate the ASS subtitles. You can edit the subtitles in ASS styling, with live preview in the windows below.
Selecting the desired line with the cursor will show that line in the preview
Custom styles can be defined, similiar to the Default style format. The first line after [V4+ Styles] are the columns, for defining the style
The first line [Events] are the columns which refer to the parameters for tuning each segment
Invalid syntax will not have any affect

<img width="1192" height="793" alt="Screenshot 2026-02-25 121618" src="https://github.com/user-attachments/assets/2dcc84b1-1f62-4b40-94ce-462d00f4f18d" />

<img width="1192" height="793" alt="Screenshot 2026-02-25 121944" src="https://github.com/user-attachments/assets/6366c73e-52aa-45ff-8140-54e31796491f" />

Click on 'Add subtitles to Video' to add the ASS subtitles to the video 
