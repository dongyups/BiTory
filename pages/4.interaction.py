import streamlit as st
st.set_page_config(layout="wide")
import openai, json, os, openai
from dotenv import load_dotenv
import utils
from PIL import Image

st.title("상호작용 🎈")

# OpenAI API 키 설정
load_dotenv(verbose=True)
openai.api_key = os.getenv("OPENAI_API_KEY")
# 변수 재사용
if "show_text" not in st.session_state:
    st.session_state.show_text = False
if "child_input" not in st.session_state:
    st.session_state.child_input = None


### 생성된 동화 로드 ###
tmp_filename = st.session_state.pv_outputs + st.session_state.session_id+"_all_prompt.json"
with open(tmp_filename, "r", encoding='utf-8') as tmpam:
    st.session_state.all_messages = json.load(tmpam)

# 최종 동화 출력
generated_korean_fairytale = []
for idx in range(len(st.session_state.all_messages)):
    if idx % 2 == 0:
        generated_korean_fairytale.append(st.session_state.all_messages[idx]['content'])
    # 글
    st.write(st.session_state.all_messages[idx]['content'])
    # 음성
    st.audio(st.session_state.pv_outputs+"voices/"+st.session_state.session_id+f"/페이지 {idx+1}.wav")
    # 그림
    if int(idx+1) in st.session_state.dict_imgs:
        resized_image = Image.open(st.session_state.dict_imgs[int(idx+1)])
        resized_image = resized_image.resize((512, 512))
        st.image(resized_image)
generated_korean_fairytale = ' '.join(generated_korean_fairytale)


### 마지막 상호작용 부분 ###
st.markdown(f"----------------------")
st.write("동화 생성이 완료되었습니다. 상호작용을 시작합니다.")
st.text("")
st.text("")
st.write("질문 생성을 하시려면 **질문 보기** 버튼을, 다시 시작을 원하시면 **재시작** 버튼을 눌러 주세요.")
st.write("**녹음시작** 버튼을 누르시면 **10초**동안 녹음됩니다. ")

create_question, restart_interact = st.columns([1,4.5])
st.text("")
with restart_interact:
    restart_interact = st.button("재시작")
    if restart_interact:
        st.session_state.pop("interaction_messages")


# 변수 재사용, 컨테이너를 사용하여 채팅 영역과 입력 영역을 분리
chat_container = st.container()
input_container = st.container()

# 세션 상태 변수 초기화
if 'interaction_messages' not in st.session_state:
    st.session_state.interaction_messages = []
    st.session_state.interaction_messages.append({"role" : "system", "content" : 
        # 아이가 생성된 동화와 가족 간의 경험, 자신의 경험, 감정을 연결하도록 유도해야해.
        # 아이에게 질문을 하고 아이의 답변을 기반으로 호응한 뒤에 제 2언어로도 말할 수 있도록 자연스럽게 유도해.
        # 호응한 뒤에 절대로 의문형 문장으로 끝내면 안돼. 
        # 부모의 선호 요소는 미국, 유아, 한국어, 영어, 날씨에 대한 표현, 풋볼 이고 아이의 선호 요소는 아이스크림, 강아지, 보라색, 블록쌓기, 루피 일때 아래와 같이 진행해.
        # 부모의 선호 요소는 중국, 유아, 한국어, 중국어, 감정 표현, 중추절 이고 아이의 선호 요소: 아이스크림, 고양이, 하늘색, 게임, 또봇 일때 아래와 같이 진행해.
        # - 부모의 선호 요소: {st.session_state.parent_prefer}
        # - 아동의 선호 요소: {st.session_state.child_prefer}
        # 이번에는 내가 한 말을 영어로 엄마에게 말해볼까? 엄마랑 같이 말해봐도 좋아! 😊
        # 😊 이제 내가 한 질문을 중국어로 엄마에게 물어봐!
        # 비슷한 말과 반대말을 한국어와 {st.session_state.select_lang_name}로 엄마에게 말해볼까? 잘 모르겠으면 엄마랑 같이 말해봐도 좋아! 😊
        f'''
        너는 아동의 한국어와 제 2언어인 {st.session_state.select_lang_name}의 언어능력을 증진시키기 위한 GPT야.
        잊지마 너는 반드시 생성된 <동화 이야기>를 참고해서 진행해야해.
        <동화 이야기>
        {generated_korean_fairytale}

        GPT의 질문은 반드시 동화 이야기를 참고해서 진행해. GPT의 질문의 수준은 아동의 눈높이에 맞는 수준으로 질문해.
        그리고 아동의 눈높이에 맞는 동사나 형용사 단어를 동화 이야기에서 하나 선택해. 선택한 단어의 유의어나 반의어를 가지고 호응할거야.
        다음의 <예시> 두가지를 참고해서 친근하게 진행해.
        <예시1>
        1. GPT의 시작: 생성된 동화는 어떠셨나요? 아이에게 한가지 질문을 해도 괜찮을까요?
        2. 부모의 답변: 네 괜찮습니다
        3. GPT의 질문: 동화에서 퍼플이 블럭으로 풋볼 경기장을 만들었어! 너는 블럭이나 장난감으로 뭘 만들어 본 적이 있어? 😊
        4. 아동의 답변: 블록으로 경찰차를 만들었어
        5. GPT의 호응: 와! 경찰차를 만들었다니 멋지다! 🚔 "만들다"와 비슷한 말은 "꾸미다"야. 이 단어를 넣어서 엄마에게 질문해 볼까? 🙋 {st.session_state.select_lang_name}로도 말해보자!

        <예시2>
        1. GPT의 시작: 생성된 동화는 어떠셨나요? 아이에게 한가지 질문을 해도 괜찮을까요?
        2. 부모의 답변: 네 좋습니다
        3. GPT의 질문: 재미있는 이야기였어! 민지가 솜이와 함께 중추절을 즐기는 모습이 정말 따뜻했어. 😊 너는 가족과 함께 특별한 날을 어떻게 보내니?
        4. 아동의 답변: 함께 맛있는 음식을 먹어
        5. GPT의 호응: 정말 좋겠다! 가족과 함께 먹는 음식은 더 맛있지. 😋 "맛있다"의 반대말은 "맛없다"야. 이 단어를 넣어서 엄마에게 질문해 볼까? 🙋 {st.session_state.select_lang_name}로도 말해보자!
        '''
    })
    st.session_state.interaction_messages.append({
        "role":"assistant", "content":"생성된 동화는 어떠셨나요? 아이에게 한가지 질문을 해도 괜찮을까요?"
    })

### 질문 생성, 부모 답변 이후 ###
with create_question:
    create_question = st.button("질문 보기")
    if create_question:
        st.session_state.interaction_messages.append({
            "role":"user", "content":"네" # 네 좋습니다 / 네 괜찮습니다
        })
        with st.spinner("질문 생성 중..."):
            llm = openai.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.interaction_messages
            )
            gpt_response = "\n".join(llm.choices[0].message.content.strip().split('\n'))
            # 응답 저장
            st.session_state.interaction_messages.append({"role": "assistant", "content": gpt_response})


# 채팅 영역에 메시지 표시
with chat_container:
    # 스크롤 가능한 영역 생성
    with st.container():
        for message in st.session_state.interaction_messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.write(message["content"])

# 입력 영역을 화면 하단에 고정
with input_container:
    # CSS로 입력창을 하단에 고정
    st.markdown(
        """
        <style>
        .stTextInput {
            position: fixed;
            bottom: 3rem;
            width: calc(100% - 15rem);
        }
        .stSpinner {
            position: fixed;
            bottom: 7rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    button_child = st.button("녹음 시작!")

    # 음성 녹음
    if button_child:
        audio_file = utils.record_audio(duration=10, fs=44100, filename=st.session_state.pv_outputs+"tmp_child_voice.wav")
        if audio_file:
            ### 한국어가 아닌 다른언어를 선택하여 진행하는것도 가능합니다 ###
            ### 그러기 위해선 프롬프트를 수정할 필요가 있습니다 ###
            user_audio = utils.recognize_speech(audio_file, target_lang="ko")
            if user_audio is not None:
                st.session_state.child_input = user_audio
                print(f"음성 입력 받음: {st.session_state.child_input}")
            else:
                st.session_state.show_text = True
        else:
            st.write("음성을 녹음하지 못했어요...")
            st.session_state.show_text = True

    # 텍스트 입력 처리
    if st.session_state.show_text:
        text_input = st.text_input("음성 인식에 실패했습니다. 텍스트로 입력해주세요:", key="text_input")
        if text_input:  # 텍스트가 입력되었을 때만
            st.session_state.child_input = text_input
            print(f"텍스트 입력 받음: {st.session_state.child_input}")
            st.session_state.show_text = False
            st.rerun()  # 화면 갱신

    if st.session_state.child_input is not None:
        # 메시지 저장 및 응답 생성
        st.session_state.interaction_messages.append({"role": "user", "content": st.session_state.child_input})
        with chat_container:
            with st.chat_message("user"):
                st.write(st.session_state.child_input)
        st.session_state.child_input=None

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("생각 중..."):
                    llm = openai.chat.completions.create(
                        model="gpt-4",
                        messages=st.session_state.interaction_messages
                    )
                    gpt_response = "\n".join(llm.choices[0].message.content.strip().split('\n'))
                    # 응답 저장
                    st.session_state.interaction_messages.append({"role": "assistant", "content": gpt_response})
                    st.write(gpt_response)


# QNA json 저장
filename_l = st.session_state.session_id + "_interaction_qna.json"
with open(st.session_state.pv_outputs + filename_l, 'w', encoding='utf-8') as f:
    json.dump(st.session_state.interaction_messages[1:], f, ensure_ascii=False, indent=4)
