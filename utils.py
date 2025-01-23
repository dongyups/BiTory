import streamlit as st
import torch, torchaudio
import uuid
import sounddevice as sd
import wave
import speech_recognition as sr
import urllib.request
import os
import re
import numpy as np


# xtts 인퍼런스
def xttsmodel_inference(tts_input: str, target_lang: str):
    # OPTIONAL: 텍스트 클리어링
    prompt= re.sub("([^\x00-\x7F]|\w)(\.|\。|\?)", r"\1\2", tts_input)
    tmp_input_path = st.session_state.pv_inputs + f"{target_lang}/"
    gpt_cond_latent, speaker_embedding = st.session_state.ttsmodel.get_conditioning_latents(
        gpt_cond_len=30, gpt_cond_chunk_len=4, max_ref_length=60,
        audio_path=[
            tmp_input_path + x for x in os.listdir(tmp_input_path)
        ]
    )
    out = st.session_state.ttsmodel.inference(
        prompt,
        target_lang,
        gpt_cond_latent,
        speaker_embedding,
        repetition_penalty=5.0,
        temperature=0.75,
    )
    return out

# xtts 결과 display 및 저장
def generate_audio(text_chunk: str, target_lang: str):
    # 몇페이지의 음성인지 파악가능
    whatpage, tts_input = text_chunk.split(":")
    aud_dest = st.session_state.pv_outputs + f"voices/{st.session_state.session_id}/"
    os.makedirs(aud_dest, exist_ok=True) # 디렉토리가 없으면 생성
    file_path_name = os.path.join(aud_dest, f"{whatpage}.wav") #최종 파일 경로
    # 인퍼런스
    out = xttsmodel_inference(tts_input, target_lang)
    # HTML Display
    st.audio(np.expand_dims(np.array(out["wav"]), 0), sample_rate=24000)
    # 자동 저장
    torchaudio.save(file_path_name, torch.tensor(out["wav"]).unsqueeze(0), 24000)


# 음성 녹음 함수 정의
def record_audio(duration, fs, filename):
    # 사용 가능한 채널 수 확인
    device_info = sd.query_devices(kind='input')
    channels = device_info['max_input_channels']  # 사용 가능한 최대 입력 채널 수
    with st.spinner("녹음중입니다..."):
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
        sd.wait()  # 녹음이 끝날 때까지 대기
    
    # WAV 파일로 저장 (wave 모듈 사용)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16비트 오디오
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
    
    st.success("녹음이 완료 되었습니다!")
    return filename


# google voice recognition 사용을 위한 언어 코드 재설정
# https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages?hl=ko
def convert_lang_code_for_google_vr(lang_code):
    if lang_code == "ar":
        return "ar-SA"
    elif lang_code == "pt":
        return "pt-PT"
    elif lang_code == "zh-cn":
        return "cmn-Hans-CN"
    elif lang_code == "cs":
        return "cs-CZ"
    elif lang_code == "nl":
        return "nl-NL"
    elif lang_code == "en":
        return "en-US"
    elif lang_code == "fr":
        return "fr-FR"
    elif lang_code == "de":
        return "de-DE"
    elif lang_code == "it":
        return "it-IT"
    elif lang_code == "pl":
        return "pl-PL"
    elif lang_code == "ru":
        return "ru-RU"
    elif lang_code == "es":
        return "es-ES"
    elif lang_code == "tr":
        return "tr-TR"
    elif lang_code == "ja":
        return "ja-JP"
    elif lang_code == "ko":
        return "ko-KR"
    elif lang_code == "hu":
        return "hu-HU"
    elif lang_code == "hi":
        return "hi-IN"
    else:
        raise ValueError("Not supported language detected.")


# 음성 인식 함수 정의
def recognize_speech(audio_file, target_lang: str):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)  # 전체 오디오 파일 읽기
    try:
        text = r.recognize_google(audio, language=convert_lang_code_for_google_vr(target_lang))
        return text
    except sr.UnknownValueError:
        st.write("음성을 인식하지 못했어요...")
        return None
    except sr.RequestError as e:
        st.write(f"Could not request results from Google Speech Recognition service; {e}")
        return None


# 이미지 생성 함수
def generate_image(word,client,setting):
    #이미지 url 저장
    image_urls = []

    #프롬프트 설정
    for pt in word:
        prom_word = pt + "in style of" + setting

        #이미지 생성 요청
        response = client.images.generate(
            model = "dall-e-3",
            prompt = prom_word,
            n=1,
            size="1024x1024"
        )

        #생성된 이미지의 url 출력
        image_url = response.data[0].url
        image_urls.append(image_url)

        #세션 ID별 디렉토리 생성
        img_dest = st.session_state.pv_outputs + f"images/{st.session_state.session_id}/" #세션 ID 기반 저장 경로
        os.makedirs(img_dest, exist_ok=True) # 디렉토리가 없으면 생성

        #고유한 파일 이름 생성
        unique_id = str(uuid.uuid4()) #UUID로 고유 이름 생성
        file_path = os.path.join(img_dest, f"{unique_id}.jpg") #최종 파일 경로

        #이미지 다운로드 및 저장
        urllib.request.urlretrieve(image_url, file_path)

    return image_urls


# 이미지 프롬프트 정화
def sanitize_prompt(prompt):
    prohibited_words = ["흥분", "촉수"]  # 금지된 단어 목록

    # 만약 prompt가 리스트일 경우 각 요소에 대해 replace 적용
    if isinstance(prompt, list):
        sanitized_prompt = [sanitize_prompt(item) for item in prompt]  # 각 요소에 대해 재귀적으로 sanitize_prompt 호출
        return sanitized_prompt

    # 만약 prompt가 문자열일 경우 직접 replace 적용
    for word in prohibited_words:
        prompt = prompt.replace(word, "")

    return prompt


# gpt 응답 저장
def save_gpt_response(gpt_response, text_storage):
    for page in gpt_response:
        # 빈 줄 건너뛰기
        if not page.strip():
            continue

        # 페이지 번호와 내용 분리
        if page.startswith("페이지"):
            parts = page.split(":", 1)
            if len(parts) > 1:
                page_num = parts[0]
                content = parts[1].strip()
                text_storage.append({"role": "assistant", "content": f"{page_num}: {content}"})
            else:
                print(f"Warning: Unexpected format in line: {page}")
        else:
            print(f"Warning: Line does not start with '페이지': {page}")


# ChatMessage 객체를 딕셔너리로 변환하는 함수
def chat_message_to_dict(chat_message):
    return {
        "role": chat_message['role'],
        "content": chat_message['content']
    }


# Reference Voice Scripts
def script_sample(lang):
    if lang=="ar":
        script=[
'1. "ماذا تفعل هنا في هذا الظلام؟" سأل الأرنب بخوف. (두려움) "너 여기서 뭐 하는 거야, 이 어두움 속에서?" 토끼가 두려움에 물었다.',
'2. قالت الفراشة، "واو! ألواني أجمل في ضوء الشمس." (기쁨) 나비가 말했다, "와! 내 색깔이 햇빛에서 더 아름답네."',
'3. "توقف عن اللعب، الساعة الآن الخامسة!" صاحت الأم بقلق. (걱정) "놀이를 멈춰라, 지금은 다섯 시야!" 엄마가 걱정스럽게 외쳤다.',
'4. قالت السحابة الصغيرة، "هل يمكنني السفر مع الرياح؟" (호기심) 작은 구름이 말했다, "바람과 함께 여행할 수 있을까요?"',
'5. "يا للكارثة! لقد سقطت الكعكة في الوحل!" بكى الطفل بحزن. (슬픔) "맙소사! 케이크가 진흙 속에 떨어졌어요!" 아이가 슬프게 울었다.',
'6. تطايرت الأوراق مثل رقصة الفراشات تحت شجرة قديمة. (평온함) 나뭇잎들이 오래된 나무 아래서 나비의 춤처럼 흩날렸다.',
'7. في ليلة مقمرة، بدأ الذئب يعوي بصوتٍ مرعب. (공포) 달빛이 비추는 밤, 늑대가 무섭게 울부짖기 시작했다.',
'8. كان صوت المطر ينقر الزجاج وكأنه يهمس أسرارًا قديمة. (신비로움) 빗소리가 유리창을 두드리며 마치 오래된 비밀을 속삭이는 듯했다.',
'9. على الطريق الطويل، التقى الغريب برجل يحمل خمس شموعٍ مضاءة. (호기심) 긴 길 위에서, 낯선 이는 다섯 개의 불이 켜진 초를 든 남자를 만났다.',
'10. في اليوم الأول من الربيع، استيقظت الأزهار بابتسامة مشرقة. (희망) 봄의 첫날, 꽃들이 환한 미소로 깨어났다.',
        ]

    elif lang=="pt":
        script=[
'"Você viu o arco-íris? Ele é mágico hoje!" exclamou a menina com entusiasmo. (기쁨) "무지개 봤어? 오늘은 마법 같아!" 소녀가 신나게 외쳤다.',
'"Por que você está chorando na chuva?" perguntou o homem com curiosidade. (호기심) "왜 비 속에서 울고 있나요?" 남자가 호기심을 가지고 물었다.',
'"Pare! Esse caminho é perigoso," alertou o guia com seriedade. (걱정) "멈추세요! 이 길은 위험합니다," 가이드가 진지하게 경고했다.',
'"Eu vou embora amanhã ao amanhecer," disse o viajante com tristeza. (슬픔) "나는 내일 새벽에 떠날 거야," 여행자가 슬프게 말했다.',
'"Não toque nisso! Está quente como o fogo!" gritou a menina assustada. (두려움) "그거 만지지 마! 불처럼 뜨거워!" 소녀가 겁에 질려 외쳤다.',
'As estrelas brilhavam no céu como pequenos diamantes. (평온함) 하늘에 별들이 작은 다이아몬드처럼 빛나고 있었다.',
'Na floresta escura, ouviu-se um uivo que gelava os ossos. (공포) 어두운 숲에서 뼛속까지 얼게 만드는 울음소리가 들렸다.',
'O vento soprou forte, carregando consigo folhas secas de outubro. (쓸쓸함) 바람이 세차게 불어와 10월의 마른 나뭇잎들을 실어 날랐다.',
'Na feira, crianças riam enquanto giravam no carrossel colorido. (기쁨) 장터에서 아이들이 알록달록한 회전목마를 돌며 웃고 있었다.',
'No último dia do verão, o sol se despediu com um brilho dourado. (희망) 여름의 마지막 날, 태양이 황금빛으로 작별을 고했다.',
        ]

    elif lang=="zh-cn":
        script = [
            '“哎呀，小兔子！雨滴答滴答地下来了！” (놀람) "어머, 토끼야! 비가 똑똑 떨어지잖아!"',
            '“这只风筝能飞到月亮吗？” (기대) "이 연이 달까지 날아갈 수 있을까?"',
            '“坏狐狸偷了苹果！我要告诉妈妈！” (분노) "나쁜 여우가 사과를 훔쳤어! 엄마한테 말할 거야!"',
            '“啊呀！踩到滑滑的蜗牛了！” (놀람) "어머! 미끌미끌한 달팽이를 밟았네!"',
            '“今天是12月25日，圣诞老人呢？” (기대) "오늘은 12월 25일이야, 산타클로스는 어디 있지?"',
            '森林深处传来“咕咕”，像猫在唱歌。(평화) 숲 속에서 "구구" 소리가 고양이 노래 같았어요.',
            '月光洒在湖面，闪闪发亮。(평온) 달빛이 호수 위에 쏟아져 반짝거렸어요.',
            '“咚咚咚”，钟声响了三下。(긴장) "똥똥똥", 시계가 세 번 울렸어요.',
            '青蛙呱呱叫了一夜。(즐거움) 개구리가 밤새도록 개골개골 울었어요.',
            '小狗摇尾巴，汪汪叫，好像找到宝贝了！ (기쁨) 작은 강아지가 꼬리를 흔들며 멍멍 짖어요. 보물을 찾은 것 같아요!',
        ]

    elif lang=="cs":
        script=[
'"Proč se ta řeka třpytí tak krásně?" zeptal se chlapec zvědavě. (호기심) "왜 강이 그렇게 아름답게 반짝이는 거야?" 소년이 호기심 가득 물었다.',
'"To je ta nejkrásnější květina, jakou jsem kdy viděla!" zvolala dívka šťastně. (기쁨) "내가 본 가장 아름다운 꽃이야!" 소녀가 행복하게 외쳤다.',
'"Dávej pozor! Ten most vypadá nebezpečně," varoval muž vážně. (걱정) "조심해! 저 다리가 위험해 보여," 남자가 심각하게 경고했다.',
'"Jdu domů, zítra bude bouřka," řekla žena smutně. (슬픔) "난 집에 갈게, 내일 폭풍이 올 거래," 여자가 슬프게 말했다.',
'"Podívej! Padají vločky sněhu," vykřikl chlapec nadšeně. (기쁨) "봐봐! 눈송이가 떨어지고 있어," 소년이 신나게 외쳤다.',
'Na vrcholku hory stál starý strom, který se skláněl ve větru. (쓸쓸함) 산 꼭대기에 서 있는 오래된 나무가 바람에 흔들리고 있었다.',
'V dálce se rozléhaly zvony, oznamující konec dne. (평온함) 멀리서 하루의 끝을 알리는 종소리가 울려 퍼졌다.',
'Podzimní listy křupaly pod nohama jako suché sušenky. (따뜻함) 가을 낙엽들이 마치 바삭한 과자처럼 발밑에서 바스락거렸다.',
'Hory byly zahalené v husté mlze, jako by skrývaly staré tajemství. (신비로움) 산들이 짙은 안개에 덮여 마치 오래된 비밀을 숨기는 것 같았다.',
'Večer se vesnice ponořila do tmy a jen hvězdy osvětlovaly cestu. (희망) 저녁에 마을은 어둠에 잠기고 별들만이 길을 밝히고 있었다.',
        ]

    elif lang=="nl":
        script=[
'"Waarom glinsteren de sterren zo fel vanavond?" vroeg het meisje nieuwsgierig. (호기심) "왜 별들이 오늘 밤 이렇게 밝게 빛나는 거야?" 소녀가 호기심 가득 물었다.',
'"Kijk! De vogels vliegen samen in een grote cirkel," riep de jongen blij. (기쁨) "봐봐! 새들이 큰 원을 그리며 함께 날고 있어," 소년이 기쁘게 외쳤다.',
'"Pas op! De brug is glad door de regen," waarschuwde de moeder bezorgd. (걱정) "조심해! 다리가 비 때문에 미끄러워," 엄마가 걱정스럽게 경고했다.',
'"Ik moet nu gaan... de avond valt," zei de man verdrietig. (슬픔) "난 이제 가야 해... 저녁이 다가오고 있어," 남자가 슬프게 말했다.',
'"Nee, niet doen! Het is veel te gevaarlijk!" schreeuwde de vrouw bang. (두려움) "안 돼, 그러지 마! 그건 너무 위험해!" 여자가 겁에 질려 외쳤다.',
'De bladeren vielen zachtjes op de grond, als dansende vlinders. (평온함) 나뭇잎들이 춤추는 나비처럼 땅 위에 부드럽게 떨어졌다.',
'In het midden van het bos klonk het mysterieuze geluid van een uil. (신비로움) 숲 한가운데서 부엉이의 신비로운 소리가 들렸다.',
'De wind huilde door de bomen alsof hij verdriet droeg. (쓸쓸함) 바람이 나무 사이로 슬픔을 품고 있는 듯 울부짖었다.',
'Bij de oude vuurtoren stonden de golven hoog, alsof ze de lucht wilden raken. (긴장감) 오래된 등대 근처에서 파도들이 하늘을 닿을 듯이 높이 솟아올랐다.',
'Op een koude ochtend scheen de zon door het ijs, als een belofte van warmte. (희망) 추운 아침, 태양이 얼음 사이로 비춰 마치 따뜻함을 약속하는 듯했다.',
        ]

    elif lang=="en":
        script=[
            '"Whoosh! Did you hear that?" (놀람) 쉭! 들었어?',
            '"Eww! What’s that smell?" (혐오) 으웩! 이 냄새 뭐야?',
            '"Yippee! Zoo on Saturday!" (흥분) 얏호! 토요일에 동물원 간다!',
            '"No way! A talking rabbit?" (놀람) 설마! 말을 하는 토끼라고?',
            '"Oh, I love how the flowers smell today!" (행복) 오늘 꽃 향기가 너무 좋아!',
            'The treasure chest sparkled under the moonlight. (설렘) 보물 상자가 달빛 아래에서 반짝였어요.',
            'Crash! The blocks tumbled down. (놀람) 쾅! 블록들이 무너져 내렸어요.',
            'The diary was dated December 12th. (호기심) 그 일기는 12월 12일로 적혀 있었어요.',
            'The raindrops pattered softly, like tears on the window. (슬픔) 빗방울이 창문에 눈물처럼 부드럽게 톡톡 떨어졌어요. ',
            '"Crunch, crunch went the autumn leaves beneath her boots." (평온) 바스락바스락, 그녀의 부츠 아래에서 가을 잎사귀가 소리 냈어요. ',
        ]

    elif lang=="fr":
        script=[
'"Pourquoi la lune est-elle si brillante ce soir ?" demanda la fille avec curiosité. (호기심) "왜 달이 오늘 밤 이렇게 밝은 거야?" 소녀가 호기심 가득 물었다.',
'"Regarde ! Les papillons volent autour des fleurs," s’écria le garçon joyeusement. (기쁨) "봐봐! 나비들이 꽃들 주위를 날고 있어," 소년이 기쁘게 외쳤다.',
'"Fais attention ! Cette rivière est trop profonde," avertit le vieil homme avec inquiétude. (걱정) "조심해! 이 강은 너무 깊어," 노인이 걱정스럽게 경고했다.',
'"Je vais partir demain à l’aube," dit l’homme tristement. (슬픔) "나는 내일 새벽에 떠날 거야," 남자가 슬프게 말했다.',
'"Non ! Ne touche pas à ça, c’est brûlant !" cria la femme avec peur. (두려움) "안 돼! 그거 만지지 마, 너무 뜨거워!" 여자가 두려움에 질려 외쳤다.',
'Les feuilles tourbillonnaient dans le vent comme des danseuses gracieuses. (평온함) 나뭇잎들이 우아한 무용수처럼 바람 속에서 빙글빙글 돌았다.',
'Dans la forêt sombre, un murmure étrange se faisait entendre. (신비로움) 어두운 숲에서 이상한 속삭임이 들렸다.',
'Le crépuscule enveloppait le village d’une douce lumière orangée. (따뜻함) 황혼이 마을을 부드러운 주황빛으로 감쌌다.',
'Les vagues s’écrasaient contre les rochers avec une force brutale. (긴장감) 파도들이 거친 힘으로 바위에 부딪치고 있었다.',
'Au premier matin de printemps, les fleurs ouvraient leurs pétales avec espoir. (희망) 봄의 첫 아침, 꽃들이 희망에 찬 듯 꽃잎을 피우고 있었다.',
        ]

    elif lang=="de":
        script=[
'"Warum funkeln die Sterne heute Nacht so hell?" fragte das Mädchen neugierig. (호기심) "왜 별들이 오늘 밤 이렇게 밝게 빛나는 거야?" 소녀가 호기심 가득 물었다.',
'"Schau mal! Die Vögel fliegen im Kreis," rief der Junge fröhlich. (기쁨) "봐봐! 새들이 원을 그리며 날고 있어," 소년이 기쁘게 외쳤다.',
'"Pass auf! Der Boden ist rutschig wegen des Regens," warnte die Mutter besorgt. (걱정) "조심해! 비 때문에 바닥이 미끄러워," 엄마가 걱정스럽게 경고했다.',
'"Ich muss morgen früh gehen," sagte der Mann traurig. (슬픔) "난 내일 아침 일찍 떠나야 해," 남자가 슬프게 말했다.',
'"Nein! Geh nicht dorthin, es ist zu gefährlich!" schrie die Frau ängstlich. (두려움) "안 돼! 거기 가지 마, 너무 위험해!" 여자가 두려움에 질려 외쳤다.',
'Die Blätter tanzten im Wind wie kleine Schmetterlinge. (평온함) 나뭇잎들이 작은 나비들처럼 바람 속에서 춤추고 있었다.',
'In der dunklen Nacht hörte man das leise Heulen eines Wolfes. (신비로움) 어두운 밤, 늑대의 은은한 울음소리가 들렸다.',
'Der Herbstnebel lag wie ein weicher Teppich über den Feldern. (따뜻함) 가을 안개가 들판 위에 부드러운 양탄자처럼 깔려 있었다.',
'Die Wellen schlugen mit einer wilden Kraft gegen die Felsen. (긴장감) 파도들이 거친 힘으로 바위에 부딪쳤다.',
'Am ersten Frühlingsmorgen öffneten die Blumen ihre Blütenblätter mit Hoffnung. (희망) 봄의 첫 아침, 꽃들이 희망에 찬 듯 꽃잎을 피웠다.',
        ]

    elif lang=="it":
        script=[
'"Perché il cielo è così rosso stasera?" chiese la bambina curiosa. (호기심) "왜 하늘이 오늘 저녁 이렇게 붉은 거야?" 소녀가 호기심 가득 물었다.',
'"Guarda! Le lucciole stanno ballando nel buio," disse il ragazzo con gioia. (기쁨) "봐봐! 반딧불이가 어둠 속에서 춤추고 있어," 소년이 기쁘게 말했다.',
'"Attento! Questa strada è piena di buche," avvertì l’uomo preoccupato. (걱정) "조심해! 이 길은 구덩이가 가득해," 남자가 걱정스럽게 경고했다.',
'"Domani partirò all’alba," disse il viaggiatore tristemente. (슬픔) "내일 새벽에 떠날 거야," 여행자가 슬프게 말했다.',
'"Non toccarlo! È pericoloso!" gridò la donna spaventata. (두려움) "그거 만지지 마! 위험해!" 여자가 겁에 질려 외쳤다.',
'Le foglie cadevano lentamente, come piume nel vento. (평온함) 나뭇잎들이 깃털처럼 바람 속에서 천천히 떨어졌다.',
'Nella foresta oscura, si sentiva il canto lontano di un gufo. (신비로움) 어두운 숲에서 부엉이의 먼 노랫소리가 들렸다.',
'Il sole tramontava dietro le colline, dipingendo il cielo di arancione. (따뜻함) 해가 언덕 뒤로 지면서 하늘을 주황빛으로 물들였다.',
'Le onde si infrangevano sugli scogli con un suono assordante. (긴장감) 파도들이 귀를 찢을 듯한 소리를 내며 바위에 부딪쳤다.',
'Con l’arrivo della primavera, i fiori sbocciarono pieni di speranza. (희망) 봄이 오자 꽃들이 희망으로 가득 차 피어났다.',
        ]

    elif lang=="pl":
        script=[
'"Dlaczego gwiazdy tak mocno świecą dziś w nocy?" zapytała dziewczynka z ciekawością. (호기심) "왜 별들이 오늘 밤 이렇게 밝게 빛나는 거야?" 소녀가 호기심 가득 물었다.',
'"Spójrz! Tęcza pojawiła się na niebie!" zawołał chłopiec z radością. (기쁨) "봐봐! 무지개가 하늘에 떠 있어!" 소년이 기쁘게 외쳤다.',
'"Uważaj! Ścieżka jest bardzo śliska," ostrzegła matka z troską. (걱정) "조심해! 길이 정말 미끄러워," 엄마가 걱정스럽게 경고했다.',
'"Jutro wyjadę o świcie," powiedział mężczyzna smutno. (슬픔) "난 내일 새벽에 떠날 거야," 남자가 슬프게 말했다.',
'"Nie idź tam! To zbyt niebezpieczne!" krzyknęła kobieta przestraszona. (두려움) "거기 가지 마! 너무 위험해!" 여자가 겁에 질려 외쳤다.',
'Liście spadały na ziemię, jakby tańczyły na wietrze. (평온함) 나뭇잎들이 바람 속에서 춤을 추는 듯 땅 위로 떨어지고 있었다.',
'W głębi lasu słychać było tajemnicze pohukiwanie sowy. (신비로움) 숲 깊은 곳에서 부엉이의 신비로운 울음소리가 들렸다.',
'Zimny deszcz stukał o szyby, jakby chciał opowiedzieć starą historię. (쓸쓸함) 차가운 빗방울이 유리창을 두드리며 오래된 이야기를 들려주는 듯했다.',
'Fale uderzały o skały z ogromną siłą, rozpryskując wodę wszędzie dookoła. (긴장감) 파도들이 강렬한 힘으로 바위에 부딪히며 물을 사방으로 튀겼다.',
'Pierwszego dnia wiosny kwiaty otworzyły swoje płatki z nadzieją. (희망) 봄의 첫날, 꽃들이 희망에 가득 차 꽃잎을 활짝 피웠다.',
        ]

    elif lang=="ru":
        script=[
'"Кто там стучится? Бум-бум-бум!" (두려움) 누가 거기 두드리니? 쿵쿵쿵!',
'"Зачем ты плачешь под дождём в такой день?" (슬픔) 왜 이런 날 비를 맞으며 울고 있는 거야?',
'"Ах, посмотри, какая красивая радуга на небе!" (기쁨) 아, 봐! 하늘에 정말 아름다운 무지개가 떠 있어!',
'"Сегодня ровно пять лет с того дня, как мы встретились." (감동) 오늘이 우리가 만난 지 꼭 5년 되는 날이야.',
'"Ты слышал этот страшный звук? У-у-у!" (두려움) 저 무서운 소리 들었니? 으으으!',
'Девочка смотрела на свои мокрые ботинки, и сердце её сжималось от грусти. (슬픔) 소녀는 젖은 신발을 내려다보며 슬픔으로 가슴이 저렸다.',
'На ветру раскачивались деревья, словно они танцевали свой последний танец. (쓸쓸함) 바람에 나무들이 흔들리며 마지막 춤을 추는 듯했다.',
'Вдруг из леса вылетела сова и громко ухнула: "Ух-ух!" (놀라움) 갑자기 숲에서 올빼미가 날아 나와 크게 울었다. "우후!"',
'Котёнок прыгнул через лужу, но упал прямо в воду. (익살) 고양이 새끼가 웅덩이를 뛰어넘으려다 물속에 빠지고 말았다.',
'В тот вечер месяц светил так ярко, что можно было считать звёзды. Их было триста двадцать семь. (평온함) 그날 저녁 달이 너무 밝게 빛나서 별을 셀 수 있었다. 별은 327개였다.',
]

    elif lang=="es":
        script=[
'"¿Por qué las hojas caen tan lentamente?" preguntó el niño con curiosidad. (호기심) "왜 나뭇잎들이 이렇게 천천히 떨어지는 거야?" 소년이 호기심 가득 물었다.',
'"¡Mira! El arcoíris tiene siete colores," exclamó la niña feliz. (기쁨) "봐봐! 무지개는 일곱 가지 색이야," 소녀가 기쁘게 외쳤다.',
'"Ten cuidado, el camino está lleno de piedras," advirtió el abuelo preocupado. (걱정) "조심해, 길에 돌이 가득해," 할아버지가 걱정스럽게 경고했다.',
'"Mañana será mi último día en este pueblo," dijo la mujer con tristeza. (슬픔) "내일이 이 마을에서의 마지막 날이 될 거야," 여자가 슬프게 말했다.',
'"¡No toques esa planta! Puede ser venenosa," gritó el hombre con miedo. (두려움) "그 식물 만지지 마! 독이 있을지도 몰라," 남자가 두려움에 질려 외쳤다.',
'Las estrellas brillaban en el cielo como pequeñas linternas. (평온함) 별들이 하늘에서 작은 랜턴처럼 빛나고 있었다.',
'En la oscuridad del bosque se escuchaba el susurro del viento entre los árboles. (신비로움) 어두운 숲 속에서 바람이 나무들 사이로 속삭이는 소리가 들렸다.',
'La lluvia caía suavemente sobre las hojas, como un suave tamborileo. (따뜻함) 빗물이 나뭇잎 위로 부드럽게 떨어지며 마치 잔잔한 드럼 소리 같았다.',
'Las olas chocaban contra las rocas con una fuerza impresionante. (긴장감) 파도들이 바위에 강렬하게 부딪쳤다.',
'Con la llegada de la primavera, los campos se llenaron de flores coloridas. (희망) 봄이 오자 들판이 알록달록한 꽃들로 가득 찼다.',
        ]

    elif lang=="tr":
        script=[
'"Neden yapraklar sararıp düşüyor?" diye sordu çocuk merakla. (호기심) "왜 나뭇잎들이 노랗게 변해서 떨어지는 거야?" 아이가 호기심 가득 물었다.',
'"Bak! Gökyüzü bugün ne kadar güzel," dedi kız sevinçle. (기쁨) "봐봐! 오늘 하늘이 정말 아름다워," 소녀가 기쁘게 말했다.',
'"Dikkat et! Yol çok kaygan," diye uyardı adam endişeyle. (걱정) "조심해! 길이 너무 미끄러워," 남자가 걱정스럽게 경고했다.',
'"Yarın buradan ayrılacağım," dedi kadın üzgün bir şekilde. (슬픔) "내일 이곳을 떠날 거야," 여자가 슬픈 목소리로 말했다.',
'"Oraya gitme! Orada bir yılan var," diye bağırdı çocuk korkuyla. (두려움) "거기 가지 마! 거기에 뱀이 있어," 아이가 겁에 질려 외쳤다.',
'Rüzgar, ağaç dallarını hafifçe sallıyordu, tıpkı nazik bir dans gibi. (평온함) 바람이 나뭇가지를 부드럽게 흔들며 마치 우아한 춤 같았다.',
'Karanlık bir mağarada, damlayan suyun yankısı duyuluyordu. (신비로움) 어두운 동굴에서 떨어지는 물방울 소리가 메아리치고 있었다.',
'Yağmur camda hafif bir melodi çalıyordu, sakinleştirici bir tonda. (따뜻함) 비가 유리창 위에서 잔잔한 멜로디를 연주하며 마음을 차분하게 했다.',
'Fırtına bulutları gökyüzünü kapladı ve güçlü bir rüzgar esti. (긴장감) 폭풍 구름이 하늘을 뒤덮고 강한 바람이 불었다.',
'İlkbahar güneşi doğarken çiçekler yüzünü ışığa döndü. (희망) 봄 햇살이 떠오르자 꽃들이 빛을 향해 고개를 돌렸다.',
        ]

    elif lang=="ja":
        script = [
            '「わあ、ピカピカしてる！」 (놀람) "와, 번쩍번쩍하고 있어!"',
            '「今日は10月10日だよ！」 (기쁨) "오늘은 10월 10일이야!"',
            '「えーん、アイス溶けた！」 (슬픔/아쉬움) "엉엉, 아이스크림 녹았어!"',
            '「おばけ！？ほんとにいるの？」 (두려움) "유령?! 진짜 있는 거야?"',
            '「ぎゃあ！クモ無理！」 (혐오) "으악! 거미는 못 봐!"',
            '鐘が鳴る夜12時です。(긴장) 종이 땡 울리는 밤 12시예요.',
            '雨がしとしと降って大地を濡らします。(평온) 비가 주룩주룩 내려 대지를 적셔요.',
            '春のように風が柔らかい日です。(평화) 봄처럼 바람이 부드러운 날이에요.',
            '小さな子犬が雨の中で震えています (슬픔) 작은 강아지가 비 속에서 떨고 있어요.',
            '暗い森の中で何かがカサカサと音を立てています。(두려움) 어두운 숲 속에서 무언가가 바스락거리고 있어요.',
        ]

    elif lang=="ko":
        script = [
            '"어? 저기, 반짝반짝 별이 하늘에서 춤을 춘다!" (기쁨)',
            '"으악! 저 나무 뒤에서 뭔가 우두둑 소리가 나는데?" (두려움)',
            '"꼬르륵, 아까부터 배에서 자꾸 이상한 소리가 나네!" (민망함)',
            '"냠냠, 이 떡볶이 진짜 매워도 맛있다, 그치?" (만족)',
            '"오늘은 12월 25일, 크리스마스잖아! 선물 받으러 가자!" (신남)',
            '"똑딱, 똑딱," 시계 소리만이 밤의 고요를 깨뜨렸어요. (고독)',
            '바람이 살랑살랑 불며 꽃잎들에게 춤을 가르쳐 주었어요. (설렘)',
            '달빛 아래 연못이 반짝였어요. (평온)',
            '숲 속 새들은 슬픔을 노래했어요. (슬픔)',
            '강아지는 꼬리를 흔들며 친구들에게 "같이 놀아요!" 하고 달려갔어요. (환희)',
        ]

    elif lang=="hu":
        script=[
'"Miért suttog a szél ilyen hangosan?" kérdezte a kislány kíváncsian. (호기심) "왜 바람이 이렇게 크게 속삭이는 거야?" 소녀가 호기심 가득 물었다.',
'"Nézd! A tó olyan, mint egy tükör," kiáltotta a fiú örömmel. (기쁨) "봐봐! 호수가 마치 거울 같아," 소년이 기쁘게 외쳤다.',
'"Vigyázz! Az ösvény csúszós a sártól," figyelmeztette az anya aggódva. (걱정) "조심해! 길이 진흙 때문에 미끄러워," 엄마가 걱정스럽게 경고했다.',
'"Holnap hajnalban elindulok," mondta az utazó szomorúan. (슬픔) "내일 새벽에 떠날 거야," 여행자가 슬프게 말했다.',
'"Ne menj oda! Veszélyes lehet," kiáltotta a nő rémülten. (두려움) "거기 가지 마! 위험할 수도 있어," 여자가 겁에 질려 외쳤다.',
'Az őszi levelek puhán hullottak a földre, mintha álomba merülnének. (평온함) 가을 낙엽들이 마치 잠에 빠진 듯 부드럽게 땅에 떨어졌다.',
'Az erdő mélyén egy bagoly titokzatosan huhogott. (신비로움) 숲 깊은 곳에서 부엉이가 신비롭게 울었다.',
'A naplemente aranyszínnel festette az eget és a hegyeket. (따뜻함) 해질녘에 하늘과 산이 황금빛으로 물들었다.',
'A viharos szél fákat döntött ki, miközben az eső záporozott. (긴장감) 폭풍우가 몰아치며 나무들이 쓰러지고 비가 퍼부었다.',
'Tavasz első napján a virágok lassan kinyíltak a napfény felé fordulva. (희망) 봄의 첫날, 꽃들이 햇빛을 향해 천천히 피어났다.',
        ]

    elif lang=="hi":
        script=[
'"आसमान इतना नीला क्यों है?" लड़की ने उत्सुकता से पूछा। (호기심) "하늘이 왜 이렇게 파란 거야?" 소녀가 호기심 가득 물었다.',
'"देखो! तितलियाँ फूलों के चारों ओर उड़ रही हैं," लड़के ने खुशी से कहा। (기쁨) "봐봐! 나비들이 꽃들 주위를 날고 있어," 소년이 기쁘게 말했다.',
'"सावधान रहो! रास्ता बहुत फिसलन भरा है," माँ ने चिंता से कहा। (걱정) "조심해! 길이 정말 미끄러워," 엄마가 걱정스럽게 말했다.',
'"कल मैं सूरज निकलने से पहले चला जाऊंगा," आदमी ने दुखी होकर कहा। (슬픔) "내일 해가 뜨기 전에 떠날 거야," 남자가 슬프게 말했다.',
'"वहाँ मत जाओ! यह बहुत खतरनाक है," औरत ने डरते हुए कहा। (두려움) "거기 가지 마! 너무 위험해," 여자가 겁에 질려 말했다.',
'पत्ते धीरे-धीरे जमीन पर गिर रहे थे, जैसे वे नृत्य कर रहे हों। (평온함) 나뭇잎들이 춤을 추는 듯 천천히 땅 위로 떨어지고 있었다.',
'जंगल में एक उल्लू की आवाज रहस्यमय तरीके से गूंज रही थी। (신비로움) 숲 속에서 부엉이 소리가 신비롭게 울려 퍼지고 있었다.',
'सूरज की आखिरी किरणें पहाड़ियों को सुनहरे रंग में रंग रही थीं। (따뜻함) 해의 마지막 빛줄기가 언덕을 황금빛으로 물들이고 있었다.',
'तेज हवाओं ने पेड़ों को झुका दिया और बारिश ज़ोर से बरस रही थी। (긴장감) 강한 바람이 나무를 휘게 하고 비가 세차게 내리고 있었다.',
'वसंत के पहले दिन फूलों ने अपनी पंखुड़ियाँ खोल दीं। (희망) 봄의 첫날, 꽃들이 꽃잎을 활짝 피웠다.',
        ]

    else:
        script=[
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

    return script