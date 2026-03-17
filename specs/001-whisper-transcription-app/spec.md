# Feature Specification: Whisper Transcription App

**Feature Branch**: `001-whisper-transcription-app`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Whisper Transcription App — Specification v1.2"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record and Transcribe Speech (Priority: P1)

The user opens the app, sees a prominent Record button, and taps it to start
capturing audio from the microphone. The Record button is replaced by Accept (✓)
and Discard (✗) buttons. When the user taps Accept, recording stops and the
audio is sent to faster-whisper for transcription. The resulting text appears
in the editable output area. A loading indicator is shown while transcription
is running.

**Why this priority**: This is the core value proposition of the app — without
it, nothing else is useful.

**Independent Test**: Launch the app, click Record, speak a sentence, click
Accept, and verify the transcribed text appears in the output area. This can be
validated end-to-end with no other features needed.

**Acceptance Scenarios**:

1. **Given** the app is idle, **When** the user clicks Record, **Then** the
   Record button is hidden and Accept (✓) and Discard (✗) buttons are shown,
   and the status indicator reads "Recording…".
2. **Given** recording is active, **When** the user clicks Accept (✓), **Then**
   recording stops, a spinner/loading indicator appears, the audio is sent to
   faster-whisper, and the transcribed text is appended to the output area.
3. **Given** transcription is complete, **When** the text is appended, **Then**
   the app returns to idle state with the Record button visible and status reads
   "Idle".
4. **Given** the output area already contains text, **When** a new transcription
   is accepted, **Then** the new text is appended (newline separated) and no
   existing text is overwritten.

---

### User Story 2 - Discard a Recording (Priority: P2)

While recording, the user decides the captured audio is not useful and taps
Discard. The audio is thrown away, no transcription is triggered, and the app
returns to the idle state.

**Why this priority**: Discarding avoids polluting the output with unwanted
audio and is necessary for a clean workflow, but the app remains usable without
it.

**Independent Test**: Click Record, wait a few seconds, click Discard, verify
no text is added to the output area and the app returns to idle.

**Acceptance Scenarios**:

1. **Given** recording is active, **When** the user clicks Discard (✗), **Then**
   recording stops immediately, the captured audio is discarded, and no
   transcription is triggered.
2. **Given** the output area has existing text, **When** the user clicks
   Discard, **Then** the existing text is unchanged.
3. **Given** Discard was clicked, **When** the action completes, **Then** the
   app returns to idle with the Record button visible and status reads "Idle".

---

### User Story 3 - Edit and Copy Transcribed Text (Priority: P2)

The user can click into the output text area to manually correct transcription
errors. They can also copy the full contents to the clipboard via a Copy button,
or clear all text with a Clear button.

**Why this priority**: These are productivity essentials — raw transcriptions
often need minor corrections and users need a way to export the result.

**Independent Test**: After a transcription appears in the output area, click
into the text and edit a word, then click Copy and verify the clipboard contains
the updated text. Click Clear and verify the area is empty.

**Acceptance Scenarios**:

1. **Given** text is in the output area, **When** the user clicks into it and
   types, **Then** the text is updated inline.
2. **Given** text is in the output area, **When** the user clicks Copy to
   Clipboard, **Then** the full text content is placed on the system clipboard.
3. **Given** text is in the output area, **When** the user clicks Clear, **Then**
   the output area is emptied.
4. **Given** the output area is empty, **When** the user clicks Copy, **Then**
   an empty string is copied without error.

---

### User Story 4 - Switch Transcription Model (Priority: P3)

The user navigates to a Settings screen (via a gear icon or link) and selects
a different faster-whisper model (e.g., `tiny`, `base`, `small`, `medium`,
`large-v3`, `distil-large-v3`). The selected model is used for all subsequent
transcriptions.

**Why this priority**: Model switching is a power-user concern. The app is
fully functional with a sensible default (`base`).

**Independent Test**: Open Settings, change the model to `small`, return to
main screen, record and accept audio, verify the transcription completes
successfully using the newly selected model.

**Acceptance Scenarios**:

1. **Given** the user is on the main screen, **When** they tap the gear icon
   or Settings link, **Then** the Settings screen is shown with a model selector.
2. **Given** the Settings screen is open, **When** the user selects a different
   model, **Then** the selection is saved and will apply to the next
   transcription.
3. **Given** a model has been selected, **When** the user returns to the main
   screen and accepts a recording, **Then** the new model is used for
   transcription.
4. **Given** a model change was made, **When** the user does not re-transcribe,
   **Then** the existing output area text is unchanged.

---

### Edge Cases

- What happens when no microphone is detected or permission is denied?
  The app MUST show a clear, actionable error message (e.g., "Microphone
  access denied — please grant permission in system settings") and remain idle.
- What happens if the recording is very short (< 0.5s) or silent?
  The transcription engine is still called; an empty result is appended silently
  with no error shown.
- What happens if transcription fails (model error, out of memory, etc.)?
  The app MUST show a user-readable error message and return to idle without
  losing existing output text.
- What happens if the selected model files are not present locally?
  The app MUST surface a clear message indicating the model is unavailable
  and not proceed to transcription.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the user to start audio recording from the
  default system microphone via a single button tap.
- **FR-002**: System MUST display Accept (✓) and Discard (✗) controls
  immediately upon recording start, replacing the Record button.
- **FR-003**: System MUST stop recording and discard captured audio when the
  user taps Discard, returning to idle with no text changes.
- **FR-004**: System MUST stop recording, transcribe the audio via faster-whisper,
  and append the result to the output area when the user taps Accept.
- **FR-005**: System MUST display a loading/spinner indicator while transcription
  is in progress and hide it when complete.
- **FR-006**: System MUST append new transcriptions to existing output text,
  separated by a newline, without overwriting prior content.
- **FR-007**: System MUST allow the user to edit the output text area inline
  at any time (including during idle state between recordings).
- **FR-008**: System MUST provide a Copy to Clipboard button that copies the
  full output area contents to the system clipboard.
- **FR-009**: System MUST provide a Clear button that empties the output area.
- **FR-010**: System MUST display a status indicator reflecting the current
  state: Idle, Recording, or Transcribing.
- **FR-011**: System MUST provide a Settings screen accessible from the main
  screen via a gear icon or Settings link.
- **FR-012**: Settings MUST include a model selector offering at minimum:
  tiny, base, small, medium, large-v3, distil-large-v3.
- **FR-013**: Model selection MUST apply to the next transcription only and
  MUST NOT re-transcribe existing output.
- **FR-014**: System MUST show a clear, actionable error message when microphone
  access is unavailable or denied.
- **FR-015**: System MUST show a clear, actionable error message when
  transcription fails, and return to idle without data loss.

### Key Entities

- **Recording**: A captured audio clip initiated by the Record button and ended
  by Accept or Discard. Ephemeral — not persisted after the action is taken.
- **Transcript**: A text segment produced from one Accept action. Appended to
  the Output.
- **Output**: The accumulated, user-editable text in the output area. Represents
  all accepted transcripts for the current session.
- **Model Configuration**: The user's selected faster-whisper model identifier.
  Persisted across sessions.

## Assumptions

- Default model is `base` (good balance of speed and accuracy for first-time use).
- Transcripts are appended with a single newline separator.
- Output text is not persisted between app sessions; session-only storage is
  sufficient for v1.
- The app targets a single user on a single machine (no multi-user or sync).
- Microphone selection is out of scope; the system default microphone is used.
- The platform (Tauri, Electron, or Python GUI) is to be decided at planning
  time and does not affect this specification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can go from app launch to completed transcription in under
  60 seconds on a typical desktop machine.
- **SC-002**: Tapping Record, Accept, or Discard produces a visible UI response
  within 200ms (button state change or spinner appears).
- **SC-003**: Transcription of a 30-second audio clip completes and text appears
  in the output area within a time consistent with the selected model's
  documented speed — no artificial delays introduced by the app itself.
- **SC-004**: 100% of transcription errors and microphone failures surface a
  user-readable message; zero silent failures.
- **SC-005**: Users can copy, edit, or clear the output at any time without
  data loss or app instability.
- **SC-006**: Switching the model in Settings takes effect on the very next
  Accept action with no app restart required.
