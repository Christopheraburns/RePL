import io
import os
import audioop
import wave
import platform
import tempfile
import aifc
import subprocess
import threading
import uuid
import math
import collections
import stat
import json
import log

try: #Attempt to use Python 2 modules
    from urllib import urlencode
    from urllib2 import Request, urlopen, URLError, HTTPError
except ImportError: #Use Python 3
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError

logger = log.rLog(False)

logger.LogThis("speechrecognition class instantiated")


class WaitTimeoutError(Exception): pass


class RequestError(Exception): pass


class UnknownValueError(Exception): pass


class AudioSource(object):
    def __init__(self):
        raise NotImplementedError("this is an abstract class")

    def __enter__(self):
        raise NotImplementedError("this is an abstract class")

    def __exit__(self, exc_type, exc_val, traceback):
        raise NotImplementedError("this is an abstract class")

class Microphone(AudioSource):
    def __init__(self, device_index=None, sample_rate=None, chunk_size=1024):
        assert device_index is None or isinstance(device_index, int), "Device Index must be None or an Integer"
        assert sample_rate is None or (isinstance(sample_rate, int) and sample_rate > 0),"Sample rate must be None or a positive Integer"
        assert isinstance(chunk_size, int) and chunk_size > 0, "Chunk Size must be a positive integer"

        #setup PyAudio
        self.pyaudio_module = self.get_pyaudio()
        audio = self.pyaudio_module.PyAudio()
        try:
            count = audio.get_device_count()#obtain device count
            if device_index is not None:
                assert 0 <= device_index < count, "Device index out of range ({} devices available; device index should be between 0 and {} inclusive)".format(count, count - 1)
            if sample_rate is None: #automatically set the sample rate to teh hardware's default sample rate
                device_info = audio.get_device_info_by_index(device_index) if device_index is not None else audio.get_default_input_device_info()
                assert isinstance(device_info.get("defaultSampleRate"), (float, int)) and device_info["defaultSampleRate"] > 0, "Invalid device info returned from PyAudio: {}".format(device_info)
                sample_rate = int(device_info["defaultSampleRate"])
        except:
            audio.terminate()
            raise

        self.device_index = device_index
        self.format = self.pyaudio_module.paInt16 #16-bit int sampling
        self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(self.format) #size of each sample
        self.SAMPLE_RATE = sample_rate #sample rate in Hertz
        self.CHUNK = chunk_size #number of frames stored in each buffer

        self.audio = None
        self.stream = None

    @staticmethod
    def get_pyaudio():
        """Imports the pyAudio module and checks its version"""
        try:
            import pyaudio
        except ImportError:
            raise AttributeError("Could not find PyAudio: check installation")
        from distutils.version import LooseVersion
        if LooseVersion(pyaudio.__version__) < LooseVersion("0.2.9"):
            raise AttributeError("PyAudio 0.2.9 or later is required (found version{})".format(pyaudio.__version__))
        return pyaudio

    @staticmethod
    def list_microphone_names():
        """List of available Microphones"""
        audio = Microphone.get_pyaudio().PyAudio()
        try:
            result = []
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                result.append(device_info.get("name"))
        finally:
            audio.terminate()
        return result

    def __enter__(self):
        assert self.stream is None, "This audio source id already inside a context manager"
        self.audio = self.pyaudio_module.PyAudio()
        try:
            self.stream = Microphone.MicrophoneStream(
                self.audio.open(
                    input_device_index=self.device_index, channels=1,
                    format=self.format, rate=self.SAMPLE_RATE, frames_per_buffer=self.CHUNK,
                    input=True, #stream is an input stream
                )
            )
        except:
            self.audio.terminate()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.stream.close()
        finally:
            self.stream = None
            self.audio.terminate()

    class MicrophoneStream(object):
        def __init__(self, pyaudio_stream):
            self.pyaudio_stream = pyaudio_stream

        def read(self, size):
            return self.pyaudio_stream.read(size, exception_on_overflow=False)

        def close(self):
            try:
                if not self.pyaudio_stream.is_stopped():
                    self.pyaudio_stream.stop_stream()
            finally:
                self.pyaudio_stream.close()

class AudioFile(AudioSource):
    """
    Creates a new ``AudioFile`` instance given a WAV/AIFF/FLAC audio file ``filename_or_fileobject``. Subclass of ``AudioSource``.

    If ``filename_or_fileobject`` is a string, then it is interpreted as a path to an audio file on the filesystem. Otherwise, ``filename_or_fileobject`` should be a file-like object such as ``io.BytesIO`` or similar.

    Note that functions that read from the audio (such as ``recognizer_instance.record`` or ``recognizer_instance.listen``) will move ahead in the stream. For example, if you execute ``recognizer_instance.record(audiofile_instance, duration=10)`` twice, the first time it will return the first 10 seconds of audio, and the second time it will return the 10 seconds of audio right after that. This is always reset to the beginning when entering an ``AudioFile`` context.

    WAV files must be in PCM/LPCM format; WAVE_FORMAT_EXTENSIBLE and compressed WAV are not supported and may result in undefined behaviour.

    Both AIFF and AIFF-C (compressed AIFF) formats are supported.

    FLAC files must be in native FLAC format; OGG-FLAC is not supported and may result in undefined behaviour.
    """

    def __init__(self, filename_or_fileobject):
        assert isinstance(filename_or_fileobject, (type(""), type(u""))) or hasattr(filename_or_fileobject, "read"), "Given audio file must be a filename string or a file-like object"
        self.filename_or_fileobject = filename_or_fileobject
        self.stream = None
        self.DURATION = None

    def __enter__(self):
        assert self.stream is None, "This audio source is already inside a context manager"
        try:
            # attempt to read the file as WAV
            self.audio_reader = wave.open(self.filename_or_fileobject, "rb")
            self.little_endian = True  # RIFF WAV is a little-endian format (most ``audioop`` operations assume that the frames are stored in little-endian form)
        except (wave.Error, EOFError):
            try:
                # attempt to read the file as AIFF
                self.audio_reader = aifc.open(self.filename_or_fileobject, "rb")
                self.little_endian = False  # AIFF is a big-endian format
            except (aifc.Error, EOFError):
                # attempt to read the file as FLAC
                if hasattr(self.filename_or_fileobject, "read"):
                    flac_data = self.filename_or_fileobject.read()
                else:
                    with open(self.filename_or_fileobject, "rb") as f: flac_data = f.read()

                # run the FLAC converter with the FLAC data to get the AIFF data
                flac_converter = get_flac_converter()
                process = subprocess.Popen([
                    flac_converter,
                    "--stdout", "--totally-silent",  # put the resulting AIFF file in stdout, and make sure it's not mixed with any program output
                    "--decode", "--force-aiff-format",  # decode the FLAC file into an AIFF file
                    "-",  # the input FLAC file contents will be given in stdin
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                aiff_data, stderr = process.communicate(flac_data)
                aiff_file = io.BytesIO(aiff_data)
                try:
                    self.audio_reader = aifc.open(aiff_file, "rb")
                except (aifc.Error, EOFError):
                    raise ValueError("Audio file could not be read as PCM WAV, AIFF/AIFF-C, or Native FLAC; check if file is corrupted or in another format")
                self.little_endian = False  # AIFF is a big-endian format
        assert 1 <= self.audio_reader.getnchannels() <= 2, "Audio must be mono or stereo"
        self.SAMPLE_WIDTH = self.audio_reader.getsampwidth()

        # 24-bit audio needs some special handling for old Python versions (workaround for https://bugs.python.org/issue12866)
        samples_24_bit_pretending_to_be_32_bit = False
        if self.SAMPLE_WIDTH == 3:  # 24-bit audio
            try: audioop.bias(b"", self.SAMPLE_WIDTH, 0)  # test whether this sample width is supported (for example, ``audioop`` in Python 3.3 and below don't support sample width 3, while Python 3.4+ do)
            except audioop.error:  # this version of audioop doesn't support 24-bit audio (probably Python 3.3 or less)
                samples_24_bit_pretending_to_be_32_bit = True  # while the ``AudioFile`` instance will outwardly appear to be 32-bit, it will actually internally be 24-bit
                self.SAMPLE_WIDTH = 4  # the ``AudioFile`` instance should present itself as a 32-bit stream now, since we'll be converting into 32-bit on the fly when reading

        self.SAMPLE_RATE = self.audio_reader.getframerate()
        self.CHUNK = 4096
        self.FRAME_COUNT = self.audio_reader.getnframes()
        self.DURATION = self.FRAME_COUNT / float(self.SAMPLE_RATE)
        self.stream = AudioFile.AudioFileStream(self.audio_reader, self.little_endian, samples_24_bit_pretending_to_be_32_bit)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self.filename_or_fileobject, "read"):  # only close the file if it was opened by this class in the first place (if the file was originally given as a path)
            self.audio_reader.close()
        self.stream = None
        self.DURATION = None

    class AudioFileStream(object):
        def __init__(self, audio_reader, little_endian, samples_24_bit_pretending_to_be_32_bit):
            self.audio_reader = audio_reader  # an audio file object (e.g., a `wave.Wave_read` instance)
            self.little_endian = little_endian  # whether the audio data is little-endian (when working with big-endian things, we'll have to convert it to little-endian before we process it)
            self.samples_24_bit_pretending_to_be_32_bit = samples_24_bit_pretending_to_be_32_bit  # this is true if the audio is 24-bit audio, but 24-bit audio isn't supported, so we have to pretend that this is 32-bit audio and convert it on the fly

        def read(self, size=-1):
            buffer = self.audio_reader.readframes(self.audio_reader.getnframes() if size == -1 else size)
            if not isinstance(buffer, bytes): buffer = b""  # workaround for https://bugs.python.org/issue24608

            sample_width = self.audio_reader.getsampwidth()
            if not self.little_endian:  # big endian format, convert to little endian on the fly
                if hasattr(audioop,
                           "byteswap"):  # ``audioop.byteswap`` was only added in Python 3.4 (incidentally, that also means that we don't need to worry about 24-bit audio being unsupported, since Python 3.4+ always has that functionality)
                    buffer = audioop.byteswap(buffer, sample_width)
                else:  # manually reverse the bytes of each sample, which is slower but works well enough as a fallback
                    buffer = buffer[sample_width - 1::-1] + b"".join(
                        buffer[i + sample_width:i:-1] for i in range(sample_width - 1, len(buffer), sample_width))

            # workaround for https://bugs.python.org/issue12866
            if self.samples_24_bit_pretending_to_be_32_bit:  # we need to convert samples from 24-bit to 32-bit before we can process them with ``audioop`` functions
                buffer = b"".join("\x00" + buffer[i:i + sample_width] for i in range(0, len(buffer),
                                                                                     sample_width))  # since we're in little endian, we prepend a zero byte to each 24-bit sample to get a 32-bit sample
            if self.audio_reader.getnchannels() != 1:  # stereo audio
                buffer = audioop.tomono(buffer, sample_width, 1, 1)  # convert stereo audio data to mono
            return buffer

class AudioData(object):
    """
        Creates a new ``AudioData`` instance, which represents mono audio data.

        The raw audio data is specified by ``frame_data``, which is a sequence of bytes representing audio samples. This is the frame data structure used by the PCM WAV format.

        The width of each sample, in bytes, is specified by ``sample_width``. Each group of ``sample_width`` bytes represents a single audio sample.

        The audio data is assumed to have a sample rate of ``sample_rate`` samples per second (Hertz).

        Usually, instances of this class are obtained from ``recognizer_instance.record`` or ``recognizer_instance.listen``, or in the callback for ``recognizer_instance.listen_in_background``, rather than instantiating them directly.
        """

    def __init__(self, frame_data, sample_rate, sample_width):
        assert sample_rate > 0, "Sample rate must be a positive integer"
        assert sample_width % 1 == 0 and 1 <= sample_width <= 4, "Sample width must be between 1 and 4 inclusive"
        self.frame_data = frame_data
        self.sample_rate = sample_rate
        self.sample_width = int(sample_width)

    def get_raw_data(self, convert_rate=None, convert_width=None):
        """
        Returns a byte string representing the raw frame data for the audio represented by the ``AudioData`` instance.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        Writing these bytes directly to a file results in a valid `RAW/PCM audio file <https://en.wikipedia.org/wiki/Raw_audio_format>`__.
        """
        assert convert_rate is None or convert_rate > 0, "Sample rate to convert to must be a positive integer"
        assert convert_width is None or (
        convert_width % 1 == 0 and 1 <= convert_width <= 4), "Sample width to convert to must be between 1 and 4 inclusive"

        raw_data = self.frame_data

        # make sure unsigned 8-bit audio (which uses unsigned samples) is handled like higher sample width audio (which uses signed samples)
        if self.sample_width == 1:
            raw_data = audioop.bias(raw_data, 1,
                                    -128)  # subtract 128 from every sample to make them act like signed samples

        # resample audio at the desired rate if specified
        if convert_rate is not None and self.sample_rate != convert_rate:
            raw_data, _ = audioop.ratecv(raw_data, self.sample_width, 1, self.sample_rate, convert_rate, None)

        # convert samples to desired sample width if specified
        if convert_width is not None and self.sample_width != convert_width:
            if convert_width == 3:  # we're converting the audio into 24-bit (workaround for https://bugs.python.org/issue12866)
                raw_data = audioop.lin2lin(raw_data, self.sample_width,
                                           4)  # convert audio into 32-bit first, which is always supported
                try:
                    audioop.bias(b"", 3,
                                 0)  # test whether 24-bit audio is supported (for example, ``audioop`` in Python 3.3 and below don't support sample width 3, while Python 3.4+ do)
                except audioop.error:  # this version of audioop doesn't support 24-bit audio (probably Python 3.3 or less)
                    raw_data = b"".join(raw_data[i + 1:i + 4] for i in range(0, len(raw_data),
                                                                             4))  # since we're in little endian, we discard the first byte from each 32-bit sample to get a 24-bit sample
                else:  # 24-bit audio fully supported, we don't need to shim anything
                    raw_data = audioop.lin2lin(raw_data, self.sample_width, convert_width)
            else:
                raw_data = audioop.lin2lin(raw_data, self.sample_width, convert_width)

        # if the output is 8-bit audio with unsigned samples, convert the samples we've been treating as signed to unsigned again
        if convert_width == 1:
            raw_data = audioop.bias(raw_data, 1,
                                    128)  # add 128 to every sample to make them act like unsigned samples again

        return raw_data

    def get_wav_data(self, convert_rate=None, convert_width=None):
        """
        Returns a byte string representing the contents of a WAV file containing the audio represented by the ``AudioData`` instance.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        Writing these bytes directly to a file results in a valid `WAV file <https://en.wikipedia.org/wiki/WAV>`__.
        """
        raw_data = self.get_raw_data(convert_rate, convert_width)
        sample_rate = self.sample_rate if convert_rate is None else convert_rate
        sample_width = self.sample_width if convert_width is None else convert_width

        # generate the WAV file contents
        with io.BytesIO() as wav_file:
            wav_writer = wave.open(wav_file, "wb")
            try:  # note that we can't use context manager, since that was only added in Python 3.4
                wav_writer.setframerate(sample_rate)
                wav_writer.setsampwidth(sample_width)
                wav_writer.setnchannels(1)
                wav_writer.writeframes(raw_data)
                wav_data = wav_file.getvalue()
            finally:  # make sure resources are cleaned up
                wav_writer.close()
        return wav_data

    def get_aiff_data(self, convert_rate=None, convert_width=None):
        """
        Returns a byte string representing the contents of an AIFF-C file containing the audio represented by the ``AudioData`` instance.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        Writing these bytes directly to a file results in a valid `AIFF-C file <https://en.wikipedia.org/wiki/Audio_Interchange_File_Format>`__.
        """
        raw_data = self.get_raw_data(convert_rate, convert_width)
        sample_rate = self.sample_rate if convert_rate is None else convert_rate
        sample_width = self.sample_width if convert_width is None else convert_width

        # the AIFF format is big-endian, so we need to covnert the little-endian raw data to big-endian
        if hasattr(audioop, "byteswap"):  # ``audioop.byteswap`` was only added in Python 3.4
            raw_data = audioop.byteswap(raw_data, sample_width)
        else:  # manually reverse the bytes of each sample, which is slower but works well enough as a fallback
            raw_data = raw_data[sample_width - 1::-1] + b"".join(
                raw_data[i + sample_width:i:-1] for i in range(sample_width - 1, len(raw_data), sample_width))

        # generate the AIFF-C file contents
        with io.BytesIO() as aiff_file:
            aiff_writer = aifc.open(aiff_file, "wb")
            try:  # note that we can't use context manager, since that was only added in Python 3.4
                aiff_writer.setframerate(sample_rate)
                aiff_writer.setsampwidth(sample_width)
                aiff_writer.setnchannels(1)
                aiff_writer.writeframes(raw_data)
                aiff_data = aiff_file.getvalue()
            finally:  # make sure resources are cleaned up
                aiff_writer.close()
        return aiff_data

    def get_flac_data(self, convert_rate=None, convert_width=None):
        """
        Returns a byte string representing the contents of a FLAC file containing the audio represented by the ``AudioData`` instance.

        Note that 32-bit FLAC is not supported. If the audio data is 32-bit and ``convert_width`` is not specified, then the resulting FLAC will be a 24-bit FLAC.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        Writing these bytes directly to a file results in a valid `FLAC file <https://en.wikipedia.org/wiki/FLAC>`__.
        """
        assert convert_width is None or (
        convert_width % 1 == 0 and 1 <= convert_width <= 3), "Sample width to convert to must be between 1 and 3 inclusive"

        if self.sample_width > 3 and convert_width is None:  # resulting WAV data would be 32-bit, which is not convertable to FLAC using our encoder
            convert_width = 3  # the largest supported sample width is 24-bit, so we'll limit the sample width to that

        # run the FLAC converter with the WAV data to get the FLAC data
        wav_data = self.get_wav_data(convert_rate, convert_width)
        flac_converter = get_flac_converter()
        process = subprocess.Popen([
            flac_converter,
            "--stdout", "--totally-silent",
            # put the resulting FLAC file in stdout, and make sure it's not mixed with any program output
            "--best",  # highest level of compression available
            "-",  # the input FLAC file contents will be given in stdin
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        flac_data, stderr = process.communicate(wav_data)
        return flac_data

    class Recognizer(AudioSource):
        def __init__(self):
            """
            Creates a new ``Recognizer`` instance, which represents a collection of speech recognition functionality.
            """
            self.energy_threshold = 300  # minimum audio energy to consider for recording
            self.dynamic_energy_threshold = True
            self.dynamic_energy_adjustment_damping = 0.15
            self.dynamic_energy_ratio = 1.5
            self.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
            self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it times out, or ``None`` for no timeout

            self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
            self.non_speaking_duration = 0.5  # seconds of non-speaking audio to keep on both sides of the recording

        def record(self, source, duration=None, offset=None):
            """
            Records up to ``duration`` seconds of audio from ``source`` (an ``AudioSource`` instance) starting at ``offset`` (or at the beginning if not specified) into an ``AudioData`` instance, which it returns.

            If ``duration`` is not specified, then it will record until there is no more audio input.
            """
            assert isinstance(source, AudioSource), "Source must be an audio source"
            assert source.stream is not None, "Audio source must be entered before recording, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"

            frames = io.BytesIO()
            seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
            elapsed_time = 0
            offset_time = 0
            offset_reached = False
            while True:  # loop for the total number of chunks needed
                if offset and not offset_reached:
                    offset_time += seconds_per_buffer
                    if offset_time > offset:
                        offset_reached = True

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break

                if offset_reached or not offset:
                    elapsed_time += seconds_per_buffer
                    if duration and elapsed_time > duration: break

                    frames.write(buffer)

            frame_data = frames.getvalue()
            frames.close()
            return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

        def adjust_for_ambient_noise(self, source, duration=1):
            """
            Adjusts the energy threshold dynamically using audio from ``source`` (an ``AudioSource`` instance) to account for ambient noise.

            Intended to calibrate the energy threshold with the ambient energy level. Should be used on periods of audio without speech - will stop early if any speech is detected.

            The ``duration`` parameter is the maximum number of seconds that it will dynamically adjust the threshold for before returning. This value should be at least 0.5 in order to get a representative sample of the ambient noise.
            """
            assert isinstance(source, AudioSource), "Source must be an audio source"
            assert source.stream is not None, "Audio source must be entered before adjusting, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
            assert self.pause_threshold >= self.non_speaking_duration >= 0

            seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
            elapsed_time = 0

            # adjust energy threshold until a phrase starts
            while True:
                elapsed_time += seconds_per_buffer
                if elapsed_time > duration: break
                buffer = source.stream.read(source.CHUNK)
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal

                # dynamically adjust the energy threshold using asymmetric weighted average
                damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
                target_energy = energy * self.dynamic_energy_ratio
                self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

        def listen(self, source, timeout=None, phrase_time_limit=None):
            """
            Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

            This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.

            The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.

            The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.

            This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising an exception.
            """
            assert isinstance(source, AudioSource), "Source must be an audio source"
            assert source.stream is not None, "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
            assert self.pause_threshold >= self.non_speaking_duration >= 0

            seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
            pause_buffer_count = int(math.ceil(
                self.pause_threshold / seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
            phrase_buffer_count = int(math.ceil(
                self.phrase_threshold / seconds_per_buffer))  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
            non_speaking_buffer_count = int(math.ceil(
                self.non_speaking_duration / seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase

            # read audio input for phrases until there is a phrase that is long enough
            elapsed_time = 0  # number of seconds of audio read
            buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read
            while True:
                frames = collections.deque()

                # store audio input until the phrase starts
                while True:
                    # handle waiting too long for phrase by raising an exception
                    elapsed_time += seconds_per_buffer
                    if timeout and elapsed_time > timeout:
                        raise WaitTimeoutError("listening timed out while waiting for phrase to start")

                    buffer = source.stream.read(source.CHUNK)
                    if len(buffer) == 0: break  # reached end of the stream
                    frames.append(buffer)
                    if len(
                            frames) > non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
                        frames.popleft()

                    # detect whether speaking has started on audio input
                    energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal
                    if energy > self.energy_threshold: break

                    # dynamically adjust the energy threshold using asymmetric weighted average
                    if self.dynamic_energy_threshold:
                        damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
                        target_energy = energy * self.dynamic_energy_ratio
                        self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

                # read audio input until the phrase ends
                pause_count, phrase_count = 0, 0
                phrase_start_time = elapsed_time
                while True:
                    # handle phrase being too long by cutting off the audio
                    elapsed_time += seconds_per_buffer
                    if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
                        break

                    buffer = source.stream.read(source.CHUNK)
                    if len(buffer) == 0: break  # reached end of the stream
                    frames.append(buffer)
                    phrase_count += 1

                    # check if speaking has stopped for longer than the pause threshold on the audio input
                    energy = audioop.rms(buffer,
                                         source.SAMPLE_WIDTH)  # unit energy of the audio signal within the buffer
                    if energy > self.energy_threshold:
                        pause_count = 0
                    else:
                        pause_count += 1
                    if pause_count > pause_buffer_count:  # end of the phrase
                        break

                # check how long the detected phrase is, and retry listening if the phrase is too short
                phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
                if phrase_count >= phrase_buffer_count or len(
                    buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

            # obtain frame data
            for i in range(
                        pause_count - non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
            frame_data = b"".join(list(frames))

            return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

        def listen_in_background(self, source, callback, phrase_time_limit=None):
            """
            Spawns a thread to repeatedly record phrases from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance and call ``callback`` with that ``AudioData`` instance as soon as each phrase are detected.

            Returns a function object that, when called, requests that the background listener thread stop, and waits until it does before returning. The background thread is a daemon and will not stop the program from exiting if there are no other non-daemon threads.

            Phrase recognition uses the exact same mechanism as ``recognizer_instance.listen(source)``. The ``phrase_time_limit`` parameter works in the same way as the ``phrase_time_limit`` parameter for ``recognizer_instance.listen(source)``, as well.

            The ``callback`` parameter is a function that should accept two parameters - the ``recognizer_instance``, and an ``AudioData`` instance representing the captured audio. Note that ``callback`` function will be called from a non-main thread.
            """
            assert isinstance(source, AudioSource), "Source must be an audio source"
            running = [True]

            def threaded_listen():
                with source as s:
                    while running[0]:
                        try:  # listen for 1 second, then check again if the stop function has been called
                            audio = self.listen(s, 1)
                        except WaitTimeoutError:  # listening timed out, just try again
                            pass
                        else:
                            if running[0]: callback(self, audio)

            def stopper():
                running[0] = False
                listener_thread.join()  # block until the background thread is done, which can be up to 1 second

            listener_thread = threading.Thread(target=threaded_listen)
            listener_thread.daemon = True
            listener_thread.start()
            return stopper

        def recognize_sphinx(self, audio_data, language="en-US", keyword_entries=None, show_all=False):
            """
            Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using CMU Sphinx.

            The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` or ``"en-GB"``, defaulting to US English. Out of the box, only ``en-US`` is supported. See `Notes on using `PocketSphinx <https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst>`__ for information about installing other languages. This document is also included under ``reference/pocketsphinx.rst``.

            If specified, the keywords to search for are determined by ``keyword_entries``, an iterable of tuples of the form ``(keyword, sensitivity)``, where ``keyword`` is a phrase, and ``sensitivity`` is how sensitive to this phrase the recognizer should be, on a scale of 0 (very insensitive, more false negatives) to 1 (very sensitive, more false positives) inclusive. If not specified or ``None``, no keywords are used and Sphinx will simply transcribe whatever words it recognizes. Specifying ``keyword_entries`` is more accurate than just looking for those same keywords in non-keyword-based transcriptions, because Sphinx knows specifically what sounds to look for.

            Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the Sphinx ``pocketsphinx.pocketsphinx.Decoder`` object resulting from the recognition.

            Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RequestError`` exception if there are any issues with the Sphinx installation.
            """
            assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
            assert isinstance(language, str), "``language`` must be a string"
            assert keyword_entries is None or all(
                isinstance(keyword, (type(""), type(u""))) and 0 <= sensitivity <= 1 for keyword, sensitivity in
                keyword_entries), "``keyword_entries`` must be ``None`` or a list of pairs of strings and numbers between 0 and 1"

            # import the PocketSphinx speech recognition module
            try:
                from pocketsphinx import pocketsphinx
            except ImportError:
                raise RequestError("missing PocketSphinx module: ensure that PocketSphinx is set up correctly.")
            except ValueError:
                raise RequestError(
                    "bad PocketSphinx installation detected; make sure you have PocketSphinx version 0.0.9 or better.")

            language_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pocketsphinx-data",
                                              language)
            if not os.path.isdir(language_directory):
                raise RequestError("missing PocketSphinx language data directory: \"{}\"".format(language_directory))
            acoustic_parameters_directory = os.path.join(language_directory, "acoustic-model")
            if not os.path.isdir(acoustic_parameters_directory):
                raise RequestError("missing PocketSphinx language model parameters directory: \"{}\"".format(
                    acoustic_parameters_directory))
            language_model_file = os.path.join(language_directory, "language-model.lm.bin")
            if not os.path.isfile(language_model_file):
                raise RequestError("missing PocketSphinx language model file: \"{}\"".format(language_model_file))
            phoneme_dictionary_file = os.path.join(language_directory, "pronounciation-dictionary.dict")
            if not os.path.isfile(phoneme_dictionary_file):
                raise RequestError(
                    "missing PocketSphinx phoneme dictionary file: \"{}\"".format(phoneme_dictionary_file))

            # create decoder object
            config = pocketsphinx.Decoder.default_config()
            config.set_string("-hmm",
                              acoustic_parameters_directory)  # set the path of the hidden Markov model (HMM) parameter files
            config.set_string("-lm", language_model_file)
            config.set_string("-dict", phoneme_dictionary_file)
            config.set_string("-logfn", os.devnull)  # disable logging (logging causes unwanted output in terminal)
            decoder = pocketsphinx.Decoder(config)

            # obtain audio data
            raw_data = audio_data.get_raw_data(convert_rate=16000,
                                               convert_width=2)  # the included language models require audio to be 16-bit mono 16 kHz in little-endian format

            # obtain recognition results
            if keyword_entries is not None:  # explicitly specified set of keywords
                with tempfile.NamedTemporaryFile("w") as f:
                    # generate a keywords file - Sphinx documentation recommendeds sensitivities between 1e-50 and 1e-5
                    f.writelines("{} /1e{}/\n".format(keyword, 100 * sensitivity - 110) for keyword, sensitivity in
                                 keyword_entries)
                    f.flush()

                    # perform the speech recognition with the keywords file (this is inside the context manager so the file isn;t deleted until we're done)
                    decoder.set_kws("keywords", f.name)
                    decoder.set_search("keywords")
                    decoder.start_utt()  # begin utterance processing
                    decoder.process_raw(raw_data, False,
                                        True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
                    decoder.end_utt()  # stop utterance processing
            else:  # no keywords, perform freeform recognition
                decoder.start_utt()  # begin utterance processing
                decoder.process_raw(raw_data, False,
                                    True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
                decoder.end_utt()  # stop utterance processing

            if show_all: return decoder

            # return results
            hypothesis = decoder.hyp()
            if hypothesis is not None: return hypothesis.hypstr
            raise UnknownValueError()  # no transcriptions available

        def recognize_google(self, audio_data, key=None, language="en-US", show_all=False):
            assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
            assert key is None  or isinstance(key, str), "``key`` must be ``None`` or a string"
            assert isinstance(language, str), "``language`` must be a string"

            flac_data = audio_data.get_flac_data(
                convert_rate=None if audio_data.sample_rate >=8000 else 8000,
                convert_width=2
            )

            if key is None: key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
            url = "http://www.google.com/speech-api/v2/recognize?{}".format(urlencode({
                "client": "chromium",
                "lang": language,
                "key": key,
            }))
            request = Request(url, data=flac_data, headers={"Content-Type": "audio/x-flac; rate={}".format(audio_data.sample_rate)})

            #Obtain Audio Transcription results
            try:
                response = urlopen(request, timeout=self.operation_timeout)
            except HTTPError as e:
                raise RequestError("recognition request failed: {}".format(e.reason))
            except URLError as e:
                raise Recognizer("recognition connection faile: {}".format(e.reason))
            response_text = response.read().decode("utf-8")

            #ignore any blank blocks
            acutal_result = []
            for line in response_text.split("\n"):
                if not line: continue
                result = json.loads(line)["result"]
                if len(result) != 0:
                    actual_result = result[0]
                    break

            #return results
            if show_all: return actual_result
            if not isinstance(actual_result, dict) or len(actual_result.get("alternative", [])) == 0: raise UnknownValueError()

            #return alternative with highest confidence score
            best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
            if "transcript" not in best_hypothesis: raise UnknownValueError()
            return best_hypothesis["transcript"]

class Recognizer(AudioSource):
    def __init__(self):
        """
        Creates a new ``Recognizer`` instance, which represents a collection of speech recognition functionality.
        """
        self.energy_threshold = 300  # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
        self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it times out, or ``None`` for no timeout

        self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
        self.non_speaking_duration = 0.5  # seconds of non-speaking audio to keep on both sides of the recording

    def record(self, source, duration=None, offset=None):
        """
        Records up to ``duration`` seconds of audio from ``source`` (an ``AudioSource`` instance) starting at ``offset`` (or at the beginning if not specified) into an ``AudioData`` instance, which it returns.

        If ``duration`` is not specified, then it will record until there is no more audio input.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before recording, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"

        frames = io.BytesIO()
        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0
        offset_time = 0
        offset_reached = False
        while True:  # loop for the total number of chunks needed
            if offset and not offset_reached:
                offset_time += seconds_per_buffer
                if offset_time > offset:
                    offset_reached = True

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break

            if offset_reached or not offset:
                elapsed_time += seconds_per_buffer
                if duration and elapsed_time > duration: break

                frames.write(buffer)

        frame_data = frames.getvalue()
        frames.close()
        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def adjust_for_ambient_noise(self, source, duration=1):
        """
        Adjusts the energy threshold dynamically using audio from ``source`` (an ``AudioSource`` instance) to account for ambient noise.

        Intended to calibrate the energy threshold with the ambient energy level. Should be used on periods of audio without speech - will stop early if any speech is detected.

        The ``duration`` parameter is the maximum number of seconds that it will dynamically adjust the threshold for before returning. This value should be at least 0.5 in order to get a representative sample of the ambient noise.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before adjusting, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0

        # adjust energy threshold until a phrase starts
        while True:
            elapsed_time += seconds_per_buffer
            if elapsed_time > duration: break
            buffer = source.stream.read(source.CHUNK)
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal

            # dynamically adjust the energy threshold using asymmetric weighted average
            damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
            target_energy = energy * self.dynamic_energy_ratio
            self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

    def listen(self, source, timeout=None, phrase_time_limit=None):
        """
        Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

        This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.

        The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.

        The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.

        This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising an exception.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        pause_buffer_count = int(math.ceil(self.pause_threshold / seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        phrase_buffer_count = int(math.ceil(self.phrase_threshold / seconds_per_buffer))  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
        non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase

        # read audio input for phrases until there is a phrase that is long enough
        elapsed_time = 0  # number of seconds of audio read
        buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read
        while True:
            frames = collections.deque()

            # store audio input until the phrase starts
            while True:
                # handle waiting too long for phrase by raising an exception
                elapsed_time += seconds_per_buffer
                if timeout and elapsed_time > timeout:
                    raise WaitTimeoutError("listening timed out while waiting for phrase to start")

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # reached end of the stream
                frames.append(buffer)
                if len(frames) > non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
                    frames.popleft()

                # detect whether speaking has started on audio input
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal
                if energy > self.energy_threshold: break

                # dynamically adjust the energy threshold using asymmetric weighted average
                if self.dynamic_energy_threshold:
                    damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
                    target_energy = energy * self.dynamic_energy_ratio
                    self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

            # read audio input until the phrase ends
            pause_count, phrase_count = 0, 0
            phrase_start_time = elapsed_time
            while True:
                # handle phrase being too long by cutting off the audio
                elapsed_time += seconds_per_buffer
                if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
                    break

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # reached end of the stream
                frames.append(buffer)
                phrase_count += 1

                # check if speaking has stopped for longer than the pause threshold on the audio input
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # unit energy of the audio signal within the buffer
                if energy > self.energy_threshold:
                    pause_count = 0
                else:
                    pause_count += 1
                if pause_count > pause_buffer_count:  # end of the phrase
                    break

            # check how long the detected phrase is, and retry listening if the phrase is too short
            phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
            if phrase_count >= phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

        # obtain frame data
        for i in range(pause_count - non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
        frame_data = b"".join(list(frames))

        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def listen_in_background(self, source, callback, phrase_time_limit=None):
        """
        Spawns a thread to repeatedly record phrases from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance and call ``callback`` with that ``AudioData`` instance as soon as each phrase are detected.

        Returns a function object that, when called, requests that the background listener thread stop, and waits until it does before returning. The background thread is a daemon and will not stop the program from exiting if there are no other non-daemon threads.

        Phrase recognition uses the exact same mechanism as ``recognizer_instance.listen(source)``. The ``phrase_time_limit`` parameter works in the same way as the ``phrase_time_limit`` parameter for ``recognizer_instance.listen(source)``, as well.

        The ``callback`` parameter is a function that should accept two parameters - the ``recognizer_instance``, and an ``AudioData`` instance representing the captured audio. Note that ``callback`` function will be called from a non-main thread.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        running = [True]

        def threaded_listen():
            with source as s:
                while running[0]:
                    try:  # listen for 1 second, then check again if the stop function has been called
                        audio = self.listen(s, 1)
                    except WaitTimeoutError:  # listening timed out, just try again
                        pass
                    else:
                        if running[0]: callback(self, audio)

        def stopper():
            running[0] = False
            listener_thread.join()  # block until the background thread is done, which can be up to 1 second

        listener_thread = threading.Thread(target=threaded_listen)
        listener_thread.daemon = True
        listener_thread.start()
        return stopper

    def recognize_sphinx(self, audio_data, language="en-US", keyword_entries=None, show_all=False):
        """
        Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using CMU Sphinx.

        The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` or ``"en-GB"``, defaulting to US English. Out of the box, only ``en-US`` is supported. See `Notes on using `PocketSphinx <https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst>`__ for information about installing other languages. This document is also included under ``reference/pocketsphinx.rst``.

        If specified, the keywords to search for are determined by ``keyword_entries``, an iterable of tuples of the form ``(keyword, sensitivity)``, where ``keyword`` is a phrase, and ``sensitivity`` is how sensitive to this phrase the recognizer should be, on a scale of 0 (very insensitive, more false negatives) to 1 (very sensitive, more false positives) inclusive. If not specified or ``None``, no keywords are used and Sphinx will simply transcribe whatever words it recognizes. Specifying ``keyword_entries`` is more accurate than just looking for those same keywords in non-keyword-based transcriptions, because Sphinx knows specifically what sounds to look for.

        Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the Sphinx ``pocketsphinx.pocketsphinx.Decoder`` object resulting from the recognition.

        Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RequestError`` exception if there are any issues with the Sphinx installation.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
        assert isinstance(language, str), "``language`` must be a string"
        assert keyword_entries is None or all(isinstance(keyword, (type(""), type(u""))) and 0 <= sensitivity <= 1 for keyword, sensitivity in keyword_entries), "``keyword_entries`` must be ``None`` or a list of pairs of strings and numbers between 0 and 1"

        # import the PocketSphinx speech recognition module
        try:
            from pocketsphinx import pocketsphinx
        except ImportError:
            raise RequestError("missing PocketSphinx module: ensure that PocketSphinx is set up correctly.")
        except ValueError:
            raise RequestError("bad PocketSphinx installation detected; make sure you have PocketSphinx version 0.0.9 or better.")

        language_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pocketsphinx-data", language)
        if not os.path.isdir(language_directory):
            raise RequestError("missing PocketSphinx language data directory: \"{}\"".format(language_directory))
        acoustic_parameters_directory = os.path.join(language_directory, "acoustic-model")
        if not os.path.isdir(acoustic_parameters_directory):
            raise RequestError("missing PocketSphinx language model parameters directory: \"{}\"".format(acoustic_parameters_directory))
        language_model_file = os.path.join(language_directory, "language-model.lm.bin")
        if not os.path.isfile(language_model_file):
            raise RequestError("missing PocketSphinx language model file: \"{}\"".format(language_model_file))
        phoneme_dictionary_file = os.path.join(language_directory, "pronounciation-dictionary.dict")
        if not os.path.isfile(phoneme_dictionary_file):
            raise RequestError("missing PocketSphinx phoneme dictionary file: \"{}\"".format(phoneme_dictionary_file))

        # create decoder object
        config = pocketsphinx.Decoder.default_config()
        config.set_string("-hmm", acoustic_parameters_directory)  # set the path of the hidden Markov model (HMM) parameter files
        config.set_string("-lm", language_model_file)
        config.set_string("-dict", phoneme_dictionary_file)
        config.set_string("-logfn", os.devnull)  # disable logging (logging causes unwanted output in terminal)
        decoder = pocketsphinx.Decoder(config)

        # obtain audio data
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)  # the included language models require audio to be 16-bit mono 16 kHz in little-endian format

        # obtain recognition results
        if keyword_entries is not None:  # explicitly specified set of keywords
            with tempfile.NamedTemporaryFile("w") as f:
                # generate a keywords file - Sphinx documentation recommendeds sensitivities between 1e-50 and 1e-5
                f.writelines("{} /1e{}/\n".format(keyword, 100 * sensitivity - 110) for keyword, sensitivity in keyword_entries)
                f.flush()

                # perform the speech recognition with the keywords file (this is inside the context manager so the file isn;t deleted until we're done)
                decoder.set_kws("keywords", f.name)
                decoder.set_search("keywords")
                decoder.start_utt()  # begin utterance processing
                decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
                decoder.end_utt()  # stop utterance processing
        else:  # no keywords, perform freeform recognition
            decoder.start_utt()  # begin utterance processing
            decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
            decoder.end_utt()  # stop utterance processing

        if show_all: return decoder

        # return results
        hypothesis = decoder.hyp()
        if hypothesis is not None: return hypothesis.hypstr
        raise UnknownValueError()  # no transcriptions available

    def recognize_google(self, audio_data, key=None, language="en-US", show_all=False):
        """
        Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using the Google Speech Recognition API.

        The Google Speech Recognition API key is specified by ``key``. If not specified, it uses a generic key that works out of the box. This should generally be used for personal or testing purposes only, as it **may be revoked by Google at any time**.

        To obtain your own API key, simply following the steps on the `API Keys <http://www.chromium.org/developers/how-tos/api-keys>`__ page at the Chromium Developers site. In the Google Developers Console, Google Speech Recognition is listed as "Speech API".

        The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` (US English) or ``"fr-FR"`` (International French), defaulting to US English. A list of supported language tags can be found in this `StackOverflow answer <http://stackoverflow.com/a/14302134>`__.

        Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the raw API response as a JSON dictionary.

        Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RequestError`` exception if the speech recognition operation failed, if the key isn't valid, or if there is no internet connection.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
        assert key is None or isinstance(key, str), "``key`` must be ``None`` or a string"
        assert isinstance(language, str), "``language`` must be a string"

        flac_data = audio_data.get_flac_data(
            convert_rate=None if audio_data.sample_rate >= 8000 else 8000,  # audio samples must be at least 8 kHz
            convert_width=2  # audio samples must be 16-bit
        )
        if key is None: key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        url = "http://www.google.com/speech-api/v2/recognize?{}".format(urlencode({
            "client": "chromium",
            "lang": language,
            "key": key,
        }))
        request = Request(url, data=flac_data,
                          headers={"Content-Type": "audio/x-flac; rate={}".format(audio_data.sample_rate)})

        # obtain audio transcription results
        logger.LogThis("Calling Google API...")
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        logger.LogThis("speechrecognition.py:  received API response")
        response_text = response.read().decode("utf-8")
        logger.LogThis("speechrecognition.py: {}".format(response_text))

        # ignore any blank blocks
        actual_result = []
        for line in response_text.split("\n"):
            if not line: continue
            result = json.loads(line)["result"]
            if len(result) != 0:
                actual_result = result[0]
                break

        # return results
        if show_all: return actual_result
        if not isinstance(actual_result, dict) or len(
            actual_result.get("alternative", [])) == 0: raise UnknownValueError()

        # return alternative with highest confidence score
        best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
        if "transcript" not in best_hypothesis: raise UnknownValueError()
        return best_hypothesis["transcript"]

def get_flac_converter():
    """Returns the absolute path of a FLAC converter executable, or raises an OSError if none can be found."""
    flac_converter = shutil_which("flac")  # check for installed version first
    if flac_converter is None:  # flac utility is not installed
        base_path = os.path.dirname(os.path.abspath(__file__))  # directory of the current module file, where all the FLAC bundled binaries are stored
        system, machine = platform.system(), platform.machine()
        if system == "Windows" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-win32.exe")
        elif system == "Darwin" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-mac")
        elif system == "Linux" and machine in {"i686", "i786", "x86"}:
            flac_converter = os.path.join(base_path, "flac-linux-x86")
        elif system == "Linux" and machine in {"x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-linux-x86_64")
        else:  # no FLAC converter available
            raise OSError("FLAC conversion utility not available - consider installing the FLAC command line application by running `apt-get install flac` or your operating system's equivalent")

    # mark FLAC converter as executable if possible
    try:
        stat_info = os.stat(flac_converter)
        os.chmod(flac_converter, stat_info.st_mode | stat.S_IEXEC)
    except OSError: pass

    return flac_converter

def shutil_which(pgm):
    """Python 2 compatibility: backport of ``shutil.which()`` from Python 3"""
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p


# ===============================
#  backwards compatibility shims
# ===============================

WavFile = AudioFile  # WavFile was renamed to AudioFile in 3.4.1


def recognize_api(self, audio_data, client_access_token, language="en", session_id=None, show_all=False):
    wav_data = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
    url = "https://api.api.ai/v1/query"
    while True:
        boundary = uuid.uuid4().hex
        if boundary.encode("utf-8") not in wav_data: break
    if session_id is None: session_id = uuid.uuid4().hex
    data = b"--" + boundary.encode("utf-8") + b"\r\n" + b"Content-Disposition: form-data; name=\"request\"\r\n" + b"Content-Type: application/json\r\n" + b"\r\n" + b"{\"v\": \"20150910\", \"sessionId\": \"" + session_id.encode("utf-8") + b"\", \"lang\": \"" + language.encode("utf-8") + b"\"}\r\n" + b"--" + boundary.encode("utf-8") + b"\r\n" + b"Content-Disposition: form-data; name=\"voiceData\"; filename=\"audio.wav\"\r\n" + b"Content-Type: audio/wav\r\n" + b"\r\n" + wav_data + b"\r\n" + b"--" + boundary.encode("utf-8") + b"--\r\n"
    request = Request(url, data=data, headers={"Authorization": "Bearer {}".format(client_access_token), "Content-Length": str(len(data)), "Expect": "100-continue", "Content-Type": "multipart/form-data; boundary={}".format(boundary)})
    try: response = urlopen(request, timeout=10)
    except HTTPError as e: raise RequestError("recognition request failed: {}".format(e.reason))
    except URLError as e: raise RequestError("recognition connection failed: {}".format(e.reason))
    response_text = response.read().decode("utf-8")
    result = json.loads(response_text)
    if show_all: return result
    if "status" not in result or "errorType" not in result["status"] or result["status"]["errorType"] != "success":
        raise UnknownValueError()
    return result["result"]["resolvedQuery"]


Recognizer.recognize_api = classmethod(recognize_api)  # API.AI Speech Recognition is deprecated/not recommended as of 3.5.0, and currently is only optionally available for paid plans

