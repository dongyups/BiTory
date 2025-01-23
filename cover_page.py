# reference: https://huggingface.co/spaces/coqui/xtts/blob/main/app.py#L32
import streamlit as st
import warnings, os, random, argparse
from pydub import AudioSegment
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import torch, torchaudio
import numpy as np
import utils
warnings.simplefilter(action='ignore')

# 하이퍼파라미터 세팅
parser = argparse.ArgumentParser()
parser.add_argument('--seed_num', type=int, default=777, help="수정가능, 결과값 고정을 위함")
parser.add_argument('--use_gpu', action='store_true', help="True: 0번 single-GPU 사용 & False: CPU 사용")
parser.add_argument('--uv', action='store_true', help="Upload Voices instead of record: 사전녹음된 음성을 업로드하여 레퍼런스로 삼을경우 사용")
arg = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = "0" if arg.use_gpu else "-1"
torch.manual_seed(arg.seed_num)
torch.cuda.manual_seed(arg.seed_num)
torch.cuda.manual_seed_all(arg.seed_num) # if use multi-GPU
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
np.random.seed(arg.seed_num)
random.seed(arg.seed_num)


# TTS 모델 캐싱
@st.cache_resource(show_spinner=True)
def Caching_XTTS_Model():
    # 디폴트 Windows parent folder -> C:/Users/USERNAME/AppData/Local/tts
    config = XttsConfig()
    config.load_json(
        "./xtts/config.json"
    )
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config, 
        checkpoint_dir="./xtts/", 
    )
    if arg.use_gpu:
        model.cuda()
    return model
st.session_state.ttsmodel = Caching_XTTS_Model()


# 제목
st.title("TTS를 위한 음성녹음")


# Part1: 개별 분류 코드 작성
supported_languages = [
    "  : -- Select Your Language -- :  ",
    "Arabic(아랍어) : ar", 
    "Brazilian Portuguese(포르투갈어) : pt", 
    "Chinese Mandarin(중국어) : zh-cn", 
    "Czech(체코어) : cs", 
    "Dutch(네덜란드어) : nl", 
    "English(영어) : en", 
    "French(프랑스어) : fr", 
    "German(독일어) : de", 
    "Italian(이탈리아어) : it", 
    "Polish(폴란드어) : pl", 
    "Russian(러시아어) : ru", 
    "Spanish(스페인어) : es", 
    "Turkish(터키어) : tr", 
    "Japanese(일본어) : ja", 
    # "Korean(한국어) : ko", # 한국어는 모국어로 선택지에서 제외
    "Hungarian(헝가리어) : hu", 
    "Hindi(힌디어) : hi"
]
chosen_lang = st.selectbox("아이의 제2언어(Second Language) 를 선택해주세요.", supported_languages)
st.session_state.select_language = chosen_lang.split(" : ")[-1] # ex) ko
st.session_state.select_lang_name = chosen_lang.split("(")[-1].split(")")[0] # ex) 한국어

name = st.text_input("자녀분의 성함을 영어로 작성해주세요. EX) 홍길동 -> gildong hong", value="")
button0 = st.button("Confirm")
if button0:
    if st.session_state.select_language == ' ':
        st.warning("언어가 선택되지 않았습니다.", icon="⚠️")
    if name == '':
        st.warning("성함이 입력되지 않았습니다.", icon="⚠️")
    else:
        st.success(f"사용될 언어 코드와 성함: {st.session_state.select_language} & {name}")
name = "_".join(name.lower().split())

st.markdown(f"경로를 생성합니다.")
button1 = st.button("Submit")
st.session_state.pv_inputs = os.getcwd().replace("\\","/")+f"/candidates/{name}/inputs/"
st.session_state.pv_outputs = os.getcwd().replace("\\","/")+f"/candidates/{name}/outputs/"

if button1:
    # 경로설정
    os.makedirs(st.session_state.pv_inputs+"ko/", exist_ok=True)  # 개별 음성파일 저장 경로 (한국어 & 제2언어)
    os.makedirs(st.session_state.pv_inputs+f"{st.session_state.select_language}/", exist_ok=True)
    os.makedirs(st.session_state.pv_outputs, exist_ok=True) # TTS 결과파일 저장 경로
    st.success('경로 생성됨')


# Part2-1: 개별 목소리 업로드/변환 및 로컬 저장
if arg.uv:
    # 한국어
    with st.form("upload-then-clear-form-korean", clear_on_submit=True):
            file_list  = st.file_uploader(
                '한국어(Korean) 음성파일을 업로드 하세요. 여러 파일을 한번에 업로드 하셔도 됩니다.', 
                type=['m4a','wav'], accept_multiple_files=True
            )
            button2 = st.form_submit_button("Convert")
            if button2:

                # 업로드 된 파일 로컬에 저장
                for file in file_list:
                    with open(st.session_state.pv_inputs+"ko/" + file.name.lower(), 'wb') as f:
                        f.write(file.getbuffer())

                # 확장자 변환 및 trim
                for file in os.listdir(st.session_state.pv_inputs+"ko/"):
                    # m4a 파일의 경우
                    if len(file.split(".m4a")[0]) != len(file):
                        tobesaved = st.session_state.pv_inputs+"ko/" + file.split(".m4a")[0]+".wav"
                        audio = AudioSegment.from_file(st.session_state.pv_inputs+"ko/" + file, format="m4a")
                        audio.export(tobesaved, format="wav")
                        os.remove(st.session_state.pv_inputs+"ko/" + file) # m4a 파일 제거
                        audio = AudioSegment.from_wav(tobesaved)
                        audio = audio[:-200] # 윈도우 녹음기 사용시 마지막 노이즈 제거
                        audio.export(tobesaved, format="wav") # 덮어쓰기

                    # wav 파일의 경우
                    else:
                        tobesaved = st.session_state.pv_inputs+"ko/" + file
                        audio = AudioSegment.from_wav(tobesaved)
                        audio = audio[:-200] # 윈도우 녹음기 사용시 마지막 노이즈 제거
                        audio.export(tobesaved, format="wav") # 덮어쓰기

                del file_list
                st.success('변환 완료')
    # 제2언어
    with st.form("upload-then-clear-form-non-korean", clear_on_submit=True):
            file_list  = st.file_uploader(
                '선택하신 제2언어(non-Korean) 음성파일을 업로드 하세요. 여러 파일을 한번에 업로드 하셔도 됩니다.', 
                type=['m4a','wav'], accept_multiple_files=True
            )
            button3 = st.form_submit_button("Convert")
            if button3:

                # 업로드 된 파일 로컬에 저장
                for file in file_list:
                    with open(st.session_state.pv_inputs+f"{st.session_state.select_language}/" + file.name.lower(), 'wb') as f:
                        f.write(file.getbuffer())

                # 확장자 변환 및 trim
                for file in os.listdir(st.session_state.pv_inputs+f"{st.session_state.select_language}/"):
                    # m4a 파일의 경우
                    if len(file.split(".m4a")[0]) != len(file):
                        tobesaved = st.session_state.pv_inputs+f"{st.session_state.select_language}/" + file.split(".m4a")[0]+".wav"
                        audio = AudioSegment.from_file(st.session_state.pv_inputs+f"{st.session_state.select_language}/" + file, format="m4a")
                        audio.export(tobesaved, format="wav")
                        os.remove(st.session_state.pv_inputs+f"{st.session_state.select_language}/" + file) # m4a 파일 제거
                        audio = AudioSegment.from_wav(tobesaved)
                        audio = audio[:-200] # 윈도우 녹음기 사용시 마지막 노이즈 제거
                        audio.export(tobesaved, format="wav") # 덮어쓰기

                    # wav 파일의 경우
                    else:
                        tobesaved = st.session_state.pv_inputs+f"{st.session_state.select_language}/" + file
                        audio = AudioSegment.from_wav(tobesaved)
                        audio = audio[:-200] # 윈도우 녹음기 사용시 마지막 노이즈 제거
                        audio.export(tobesaved, format="wav") # 덮어쓰기

                del file_list
                st.success('변환 완료')

# Part2-2: 개별 목소리 10개씩 샘플 녹음
else: # NOT arg.uv
    st.markdown(f"----------------------")
    st.markdown(f"**목소리를 녹음하는 부분입니다. 버튼을 눌러 녹음하시면 됩니다. 다시 녹음을 원하시면 버튼을 눌러 재녹음 해주세요. 약 6초가량 녹음이 진행됩니다.**")

    st.markdown(f"한국어 예시")
    scripts_ko = utils.script_sample(lang="ko")

    st.markdown(f"**{scripts_ko[0]}**")
    ko1 = st.button("한국어 녹음1")
    if ko1:
        desired_file_name="ko1.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[1]}**")
    ko2 = st.button("한국어 녹음2")
    if ko2:
        desired_file_name="ko2.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[2]}**")
    ko3 = st.button("한국어 녹음3")
    if ko3:
        desired_file_name="ko3.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[3]}**")
    ko4 = st.button("한국어 녹음4")
    if ko4:
        desired_file_name="ko4.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[4]}**")
    ko5 = st.button("한국어 녹음5")
    if ko5:
        desired_file_name="ko5.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[5]}**")
    ko6 = st.button("한국어 녹음6")
    if ko6:
        desired_file_name="ko6.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[6]}**")
    ko7 = st.button("한국어 녹음7")
    if ko7:
        desired_file_name="ko7.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[7]}**")
    ko8 = st.button("한국어 녹음8")
    if ko8:
        desired_file_name="ko8.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[8]}**")
    ko9 = st.button("한국어 녹음9")
    if ko9:
        desired_file_name="ko9.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_ko[9]}**")
    ko10 = st.button("한국어 녹음10")
    if ko10:
        desired_file_name="ko10.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+"ko/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+"ko/"+desired_file_name, format="audio/wav")

    ###

    st.markdown(f"-")
    st.markdown(f"제2외국어 예시")
    scripts_secondlang = utils.script_sample(lang=st.session_state.select_language)

    st.markdown(f"**{scripts_secondlang[0]}**")
    sl1 = st.button("제2외국어 녹음1")
    if sl1:
        desired_file_name="sl1.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[1]}**")
    sl2 = st.button("제2외국어 녹음2")
    if sl2:
        desired_file_name="sl2.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[2]}**")
    sl3 = st.button("제2외국어 녹음3")
    if sl3:
        desired_file_name="sl3.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[3]}**")
    sl4 = st.button("제2외국어 녹음4")
    if sl4:
        desired_file_name="sl4.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[4]}**")
    sl5 = st.button("제2외국어 녹음5")
    if sl5:
        desired_file_name="sl5.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[5]}**")
    sl6 = st.button("제2외국어 녹음6")
    if sl6:
        desired_file_name="sl6.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[6]}**")
    sl7 = st.button("제2외국어 녹음7")
    if sl7:
        desired_file_name="sl7.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[7]}**")
    sl8 = st.button("제2외국어 녹음8")
    if sl8:
        desired_file_name="sl8.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[8]}**")
    sl9 = st.button("제2외국어 녹음9")
    if sl9:
        desired_file_name="sl9.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")

    st.markdown(f"**{scripts_secondlang[9]}**")
    sl10 = st.button("제2외국어 녹음10")
    if sl10:
        desired_file_name="sl10.wav"
        audio_file = utils.record_audio(duration=6.5, fs=44100, filename=st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name)
        st.audio(st.session_state.pv_inputs+f"{st.session_state.select_language}/"+desired_file_name, format="audio/wav")


# Part3: 모델 인퍼런스
# button4 = st.button("Next")
# if button4:
st.markdown(f"----------------------")
supported_sample_texts = {
    "ar": "يتم إنشاء القصص الخيالية بهذا الصوت.",
    "pt": "Histórias são geradas com esta voz.",
    "zh-cn": "通过这个声音生成童话故事。",
    "cs": "Pohádky jsou vytvořeny tímto hlasem.",
    "nl": "Sprookjes worden gegenereerd met deze stem.",
    "en": "Fairy tales are generated with this voice.",
    "fr": "Des contes de fées sont générés avec cette voix.",
    "de": "Märchen werden mit dieser Stimme erstellt.",
    "it": "Le fiabe vengono generate con questa voce.",
    "pl": "Bajki są generowane tym głosem.",
    "ru": "Сказки создаются этим голосом.",
    "es": "Los cuentos de hadas se generan con esta voz.",
    "tr": "Bu sesle masallar oluşturulur.",
    "ja": "この声で童話が生成されます。",
    "ko": "이 목소리로 동화가 생성됩니다.",
    "hu": "A mesék ezzel a hanggal jönnek létre.",
    "hi": "इस आवाज़ के साथ परियों की कहानियाँ बनाई जाती हैं।",
}

output_name = "tmp_parent_voice"
st.markdown(f"**아래 버튼을 눌러 생성된 목소리를 확인해 보세요.**")
tts_input_firstlang = st.text_area(
    "TTS로 변환할 한국어(ko) 샘플 텍스트를 입력하세요.", height=1, 
    value=supported_sample_texts["ko"]
)
if st.session_state.select_language in [*supported_sample_texts]:
    tts_input_secondlang = st.text_area(
        f"TTS로 변환할 {st.session_state.select_lang_name}({st.session_state.select_language}) 샘플 텍스트를 입력하세요.", height=1, 
        value=supported_sample_texts[st.session_state.select_language]
    )
else:
    tmp_text_area = st.text_area("TTS로 변환할 제2언어가 선택되지 않았습니다.", height=1)

button5 = st.button("Run")
if button5:
    # st.write(prompt)
    with st.spinner("변환 중..."):

        # (1) 제1언어
        st.write("한국어 레퍼런스 파일: " + ", ".join(os.listdir(st.session_state.pv_inputs+"ko/")))
        out0 = utils.xttsmodel_inference(tts_input_firstlang, "ko")
        # HTML Display
        st.audio(np.expand_dims(np.array(out0["wav"]), 0), sample_rate=24000)
        # 자동 저장
        torchaudio.save(st.session_state.pv_outputs+f"{output_name}_ko.wav", 
                        torch.tensor(out0["wav"]).unsqueeze(0), 24000)

        # (2) 제2언어
        st.write("제2언어 레퍼런스 파일: " + ", ".join(os.listdir(st.session_state.pv_inputs+f"{st.session_state.select_language}/")))
        out1 = utils.xttsmodel_inference(tts_input_secondlang, st.session_state.select_language)
        # HTML Display
        st.audio(np.expand_dims(np.array(out1["wav"]), 0), sample_rate=24000)
        # 자동 저장
        torchaudio.save(st.session_state.pv_outputs+f"{output_name}_{st.session_state.select_language}.wav", 
                        torch.tensor(out1["wav"]).unsqueeze(0), 24000)

        st.success('TTS 생성 및 저장 완료')
        st.markdown("아래의 버튼을 눌러 계속 진행해 주세요.")
        st.page_link("pages/1.parent_pref.py", label="부모 선호도 조사", icon="1️⃣")
