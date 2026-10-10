/*
VOICE_AUDIO.H

Voice chat's sound (voice_audio.c): the microphone, Opus, and the other
players' voices mixed into the game's output. Called by
port/linux/game/network_voice.c (the game's side, so its flags are int) and
dsound_sdl.c (the mix).
*/

#ifndef VOICE_AUDIO_H
#define VOICE_AUDIO_H

/* a frame: 20 ms at 48 kHz, mono */
#define VOICE_FRAME_SAMPLES 960
/* the longest packet sent or taken (64 kbps is 160 bytes a frame) */
#define VOICE_MAXIMUM_PACKET 400

/* voice_audio_microphone() result values. Permission denial is distinct from
 * a transient device-open failure so callers can retry the latter without
 * repeatedly prompting for permission. */
enum
{
	VOICE_AUDIO_MICROPHONE_DEVICE_FAILURE = -2,
	VOICE_AUDIO_MICROPHONE_PERMISSION_DENIED = -1,
	VOICE_AUDIO_MICROPHONE_NOT_READY = 0,
	VOICE_AUDIO_MICROPHONE_READY = 1,
};

/* opens the microphone (on another thread: not at once) or closes it;
returns one of the result values above */
int voice_audio_microphone(int open);
/* the next 20 ms the microphone heard, if it has them all; 1 if so */
int voice_audio_read_frame(float *frame);
/* a frame's level (its root mean square, 1 at full scale) */
float voice_audio_level(const float *frame);
/* a frame encoded at the bitrate (bits a second); its packet's length, 0
for none */
int voice_audio_encode(const float *frame, int bitrate, unsigned char *packet, int maximum);
/* a speaker's packet (speaker: any number naming them), to play at the
gain (1: as spoken) and pan (-1 left to 1 right) */
/* a packet's decoded samples queued, or 0 if it could not be played */
int voice_audio_play(int speaker, unsigned short sequence, const unsigned char *packet, int length, float gain,
	float pan);
/* a speaker no longer heard: their buffer and decoder freed; or all */
void voice_audio_forget(int speaker);
void voice_audio_forget_all(void);
/* whether a speaker's voice is playing now */
int voice_audio_speaking(int speaker);
void voice_audio_set_volume(float volume);
/* (dsound_sdl.c, on the audio thread) the voices added to the output
(stereo, 48 kHz) */
void voice_audio_mix(float *output, unsigned long frames);

#endif
