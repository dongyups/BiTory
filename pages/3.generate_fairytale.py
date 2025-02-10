import streamlit as st
import openai, os, json, random, re, uuid
from dotenv import load_dotenv
import utils

st.title("동화생성 🎈")

# api키 설정
load_dotenv(verbose=True)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 세션 상태 변수 초기화
if "img_num" not in st.session_state:
    st.session_state.img_num = []

### voice recognition 오류시 파일 수정 먼저 진행 ###
tmp_parent_prefer = st.session_state.pv_outputs + st.session_state.session_id + "_parent_prefer.json"
tmp_child_prefer = st.session_state.pv_outputs + st.session_state.session_id + "_child_prefer.json"
with open(tmp_parent_prefer, "r", encoding='utf-8') as tmppp:
    st.session_state.parent_prefer = json.load(tmppp)
with open(tmp_child_prefer, "r", encoding='utf-8') as tmpcp:
    st.session_state.child_prefer = json.load(tmpcp)
print("부모 선호도 결과:", st.session_state.parent_prefer)
print("아동 선호도 결과:", st.session_state.child_prefer)


### 동화 작성 부분 ###
# 첫번째 동화 생성
if 'first_tale' not in st.session_state:
    with st.spinner("동화 만들 재료 수집 하는 중..."):
        llm_1 = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role":"user","content": f'''
                다음 요소들을 기억해: 부모의 선호 요소: {st.session_state.parent_prefer}, 아동의 선호 요소: {st.session_state.child_prefer}
            
                그리고 다음 8가지 조건으로 동화를 구성해줘 
                1. 아동의 선호 요소를 넣어줘 
                2. ‘표현’ 을 학습할 수 있게 동화 안에 넣어줘 
                3. 부모의 ‘출신 국가’ 를 동화의 사건, 배경, 등장인물 등에 적용해줘 
                4. ‘문화’ 에 대한 설명을 자연스럽게 넣어줘 
                5. 주어진 요소들을 이름으로 사용하지 마 
                6. 등장인물들은 모두 이름을 가지고 있어야 해 
                7. 만일 아동 나이가 ‘영아’이면, 0~3세 아동이 이해하기 쉬운 표현으로 의성어와 의태어를 추가해줘 
                8. 만일 아동 나이가 ‘유아’이면, 4~7세 아동의 표현력이 향상할 수 있도록 동화를 만들어줘. 
            
                동화의 분량은 다음 조건을 지켜줘. 
                1. 만일 아동 나이가 ‘영아’이면, 총 12페이지, 각 페이지 당 글자 수는 10자 이상 40자 이하로 만들어줘. 
                2. 만일 아동 나이가 ‘유아’이면, 총 12페이지, 각 페이지 당 글자 수 20자 이상 80자 이하로 만들어줘.
                위의 조건들을 모두 포함하여 한국어로 동화를 써줘. 그리고 모든 내용은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성되게 만들어줘.
                
                만약 부모의 선호 요소가 캐나다, 유아, 한국어, 영어, 날씨에 대한 표현, 아이스 하키 이고, 
                아동의 선호 요소가 젤리, 고양이, 하늘색, 숨바꼭질, 루피 라고 한다면 동화는 다음 예시처럼 출력해줘.
                예시:
                페이지 1: 아침이 밝았어요. 오늘은 파란 하늘이 펼쳐진 맑은 날이에요. 루피는 창밖을 보며 기분이 좋아졌어요. 
                페이지 2: "오늘은 젤리와 숨바꼭질을 해야지!" 루피는 좋아하는 고양이 인형, 젤리를 꼭 안고 이야기했어요. 
                페이지 3: 루피는 젤리를 데리고 집 앞 공원으로 나갔어요. 공원에는 사람들이 아이스 하키를 즐기고 있었어요. "와, 아이스 하키야!" 루피는 눈이 반짝였어요. 
                ...
                '''
                }
            ]
        )
        first_tale = llm_1.choices[0].message.content.strip().split('\n')
        st.session_state.first_tale=first_tale

# 최종 동화 생성
if 'final_tale' not in st.session_state:
    st.session_state.final_tale = []
    with st.spinner("동화를 만들고 있는 중..."):
        llm_2 = client.chat.completions.create(
            model = "gpt-4",
            messages=[
                {"role": "system", "content": 
                f"""당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다.
                제 2언어는 {st.session_state.select_lang_name}입니다.
                다음 지시사항을 엄격히 따라 동화를 작성해주세요:
        
                1. 형식:
                - 홀수 페이지: 한국어로 작성된 내용
                - 짝수 페이지: 직전 홀수 페이지의 내용을 제 2언어로 번역
                - 각 페이지는 반드시 "페이지 N: " 형식으로 시작해야 합니다 (N은 페이지 번호)
                - 페이지 번호는 1부터 시작하여 순차적으로 증가
            
                2. 내용:
                - 부모의 선호 요소를 반드시 포함하여 주세요: {st.session_state.parent_prefer}
                - 아동의 선호 요소도 반드시 포함하여 주세요: {st.session_state.child_prefer}
                - 새로운 캐릭터를 추가하여 상호작용을 통해 동화를 더 흥미롭게 만들어주세요.
                - 새로운 사건을 추가하여 동화를 더 매력적으로 만들어주세요.
                - '자녀가 배웠으면 하는 언어 표현'과 관련된 단어 사용을 늘려 강조해주세요.
                - '자녀에게 알려주고 싶은 문화적 요소'에 대한 설명을 강화하여 강조해주세요.
                - 모든 요소들을 자연스럽게 포함시켜 동화를 진행해주세요.
            
                3. 길이: 총 24페이지 (한국어 12페이지, 제 2언어 12페이지)
            
                4. 주의사항:
                - 설명 없이 이야기만 출력해주세요.
                - 각 페이지의 내용은 2-3문장으로 제한해주세요.
            
                예시 형식:
                페이지 1: [한국어로 작성된 내용]
                페이지 2: [제 2언어로 번역된 내용]
                페이지 3: [한국어로 작성된 내용]
                ...

                이전에 생성된 동화를 기반으로 위 지시사항에 맞게 수정하여 새로운 동화를 작성해주세요.
                그리고 모든 내용은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성되게 만들어주세요.
                """
                },

                {"role": "user", "content": 
                f'''이전에 생성된 동화: {st.session_state.first_tale}
                위 지시사항에 따라 이 동화를 수정하고 확장하여 새로운 버전을 만들어주세요.
                '''}
            ]
        )
        gpt_response = llm_2.choices[0].message.content.strip().split('\n')

        # final_tale에 gpt 응답 저장
        utils.save_gpt_response(gpt_response,st.session_state.final_tale)

    # ### OPTIONAL: zh-cn 한어병음 ###
    # # 언어가 중국어일 때 한어 병음 추가
    # if st.session_state.select_language == 'zh-cn':
    #     st.session_state['messages_2'] = []

    #     # 중국어 내용만 추출
    #     chinese_content = "\n".join([page["content"] for page in st.session_state.final_tale if
    #                                  int(page["content"].split(":")[0].split()[1]) % 2 == 0])

    #     # 한어병음 생성
    #     llm_3 = client.chat.completions.create(
    #         model="gpt-4",
    #         messages=[
    #             {"role": "system", "content": "당신은 중국어 텍스트를 한어병음으로 변환하는 전문가입니다. 주어진 중국어 텍스트의 한어병음만을 제공해주세요."},
    #             {"role": "user", "content": 
    #             f'''다음 중국어 이야기의 한어병음만 출력해주세요. 각 페이지는 "페이지 N:"으로 시작해야 합니다(N은 페이지 번호).
    #             이야기:
    #             {chinese_content}
    #             '''}
    #         ]
    #     )

    #     gpt_response = llm_3.choices[0].message.content.strip().split('\n')
    #     # messages_2에 gpt 응답 한어병음 저장
    #     utils.save_gpt_response(gpt_response,st.session_state.messages_2)


### 동화 삽화 부분 ###
# 그림 스타일
if "image_style" not in st.session_state:
    style = [
        "Sebastian, children's book illustrator, Whimsical and colorful style, Medium: Watercolor, Color Scheme: Bright and lively color palette",
        "kids illustration, oil pastel in a dreamy color pallete",
        "kids illustration, colored pencil in a cute and adorable style",
        "adorable storybook illustration with large pastel, a color pencil sketch inspired by Edwin Landseer",
        "a storybook illustration by Marten Post",
        "a storybook illustration by Walt Disney, Disney Studio presents",
        "cute and simple cartoon style, in a dreamy color palette",
    ]
    st.session_state.image_style = str(random.choice(style))

# 이미지 프롬프트_페이지 추출
if 'prompt1' not in st.session_state:
    st.session_state.prompt1 = []
    with st.spinner("그림 만들 재료 수집중1..."):
        llm_4 = client.chat.completions.create(
            model = "gpt-4",
            messages= [
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role": "user", "content": f'''
                선호 요소: {st.session_state.parent_prefer} & {st.session_state.child_prefer}
                동화: {st.session_state.final_tale}
                선호 요소들을 고려해 동화에서 그림을 삽입할만한 페이지 4개를 골라주세요.
                그리고 다음의 선호 요소 예시를 참고하여 아래의 예시 형식처럼 출력해주세요.

                선호 요소 예시: 캐나다, 유아, 한국어, 영어, 날씨에 대한 표현, 아이스 하키 & 젤리, 고양이, 하늘색, 숨바꼭질, 루피
                예시 형식:
                페이지 1: 파란 하늘이 맑게 펼쳐진 아침이에요. 오늘은 날씨가 좋아서 루피가 기분이 좋아졌어요.,
                페이지 3: "오늘은 숨바꼭질을 해야겠다!" 고양이 인형을 꼭 안고 있는 루피는 놀이를 하고 싶다고 이야기했어요.,
                페이지 5: 루피는 젤리와 함께 집 앞 공원으로 나갔어요. 공원에는 아이들이 놀고 있었어요.",
                페이지 11: 공원의 한쪽에서는 피자를 먹고 있는 가족들이 있었어요. "피자 냄새가 좋아!" 루피는 냄새를 맡으며 말했어요
                '''
                }
            ]
        )
        prompt1 = llm_4.choices[0].message.content.strip().split('\n')
        st.session_state.prompt1=prompt1

# 이미지 프롬프트_캐릭터 외형
if 'prompt2' not in st.session_state:
    st.session_state.prompt2 = []
    with st.spinner("그림 만들 재료 수집중2..."):
        llm_5 = client.chat.completions.create(
            model = "gpt-4",
            messages= [
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role": "user", "content": f'''
                스토리: {st.session_state.prompt1}
                주어진 스토리에서 모든 캐릭터를 추출하고  캐릭터가 무엇인지 영어로 출력하세요.
                만일 Sam 이라는 다람쥐 캐릭터라면 ‘Sam the squirrel’ 로 출력하세요. 그리고 캐릭터의 생김새를 출력하세요.
                만일 캐릭터가 사람이라면 캐릭터의 나이, 이목구비, 헤어, 의상을 형식처럼 출력하세요.
                그리고 모든 설명은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성하세요.

                형식:
                페이지 1: (Subject) Loopy the toddler(age: 3), (Appearance) Small size,  round face, big round eyes, (Hair) soft curls in light brown (clothes) Bright pastel blue shirt
                '''
                }
            ]
        )
        prompt2 = llm_5.choices[0].message.content.strip().split('\n')
        st.session_state.prompt2=prompt2

# 이미지 프롬프트_배경
if 'prompt3' not in st.session_state:
    st.session_state.prompt3 = []
    with st.spinner("그림 만들 재료 수집중3..."):
        llm_6 = client.chat.completions.create(
            model = "gpt-4",
            messages= [
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role": "user", "content": f'''
                스토리: {st.session_state.prompt1}
                외형: {st.session_state.prompt2}

                주어진 외형을 참고해, 주어진 스토리에서 각 페이지에 해당하는 키워드를 형식처럼 영어로 작성하세요.
                그리고 모든 설명은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성하세요.

                형식:
                페이지 1: (Feeling) Happy (Action) watching the flowers, (Background) old tree (adjective) luscious (Environment) in the forest
                '''
                }
            ]
        )
        prompt3 = llm_6.choices[0].message.content.strip().split('\n')
        st.session_state.prompt3=prompt3

# 이미지 프롬프트_Wrap
if 'prompt4' not in st.session_state:
    st.session_state.prompt4 = []
    with st.spinner("그림 만들 재료 수집중4..."):
        llm_7 = client.chat.completions.create(
            model = "gpt-4",
            messages= [
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role": "user", "content": f'''
                스토리: {st.session_state.prompt1}
                외형: {st.session_state.prompt2}
                배경: {st.session_state.prompt3}
                스토리의 각 페이지마다 캐릭터 외형과 배경을 형식처럼 합쳐주세요.
                그리고 모든 설명은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성되게 만드세요.
                형식:
                페이지 1: (Subject) Loopy the toddler(age: 3), (Appearance) Small size, round face, big round eyes, (Hair) soft curls in light brown (cloth) Bright pastel blue shirt, (Feeling) Happy (Action) watching the flowers, (Background) old tree (adjective) luscious (Environment) in the forest,
                페이지 3: (Subject) Crong the playful bunny (age: 2), (Appearance) Fluffy ears, small button nose, big smile, (Color) soft cream white, (cloth) Green bow tie, (Feeling) Curious, (Action) holding a strawberry, (Background) grassy hill (adjective) gentle slope (Environment) in a sunny meadow

                '''
                }
            ]
        )
        prompt4 = llm_7.choices[0].message.content.strip().split("\n\n")
        st.session_state.prompt4=prompt4

# 이미지 번호와 내용 분리
for p in st.session_state.prompt4:
    if not p.strip():
        continue

    if p.startswith("페이지"):
        sections = p.split(":", 1)  # 첫 번째 : 까지만
        if len(sections) > 1:
            try:
                p_num = int(sections[0].replace("페이지", "").strip())  # 페이지 번호 추출
                st.session_state.img_num.append(p_num)
            except ValueError:
                print(f"Warning: Unable to parse page number in line: {p.strip()}")
        else:
            print(f"Warning: Unexpected format in line: {p.strip()}")
    else:
        print(f"Warning: Line does not start with '페이지': {p.strip()}")

#출력물 확인
print(st.session_state.img_num)  # img_num 출력
print(st.session_state.prompt4)
print(st.session_state.final_tale)


# 이미지 프롬프트 정화
ref_prompt = utils.sanitize_prompt(st.session_state.prompt4)
st.session_state.ref_prompt = ref_prompt


#이미지와 넘버 매치
urls_list = utils.generate_image(st.session_state.ref_prompt,client=client,setting=st.session_state.image_style)
num_list = st.session_state.img_num
st.session_state.dict_imgs = dict(zip(num_list, urls_list))


### 동화 최종 생성 부분 ###
# 최종 동화 출력
if st.session_state.final_tale:
    for message in st.session_state.final_tale:
        if message["role"] == "assistant":
            with st.chat_message(message["role"]):

                # 텍스트 출력
                st.write(message["content"])
                
                # 음성 출력
                # 페이지가 홀수일때(한국어 일때)의 오디오
                if int(message["content"].split(":")[0].split()[1]) % 2 == 1:
                    utils.generate_audio(message["content"], target_lang="ko")
                # 페이지가 짝수일때(제2언어 일때)의 오디오
                if int(message["content"].split(":")[0].split()[1]) % 2 == 0:
                    utils.generate_audio(message["content"], target_lang=st.session_state.select_language)

                # 이미지 생성
                if any(int(message["content"].split(":")[0].split()[1]) == int(i) for i in list(st.session_state.dict_imgs.keys())):
                    with st.spinner("그림이 나오고 있어요"):

                        # 이미지 출력
                        page_number = int(message["content"].split(":")[0].split()[1])

                        # 매칭되는 페이지 번호에 해당하는 이미지 출력
                        if page_number in st.session_state.dict_imgs:
                            st.image(st.session_state.dict_imgs[page_number], use_column_width=True)
                            
    # ### OPTIONAL: zh-cn 한어병음 ###
    # # 한어 병음 출력
    # if "messages_2" in st.session_state:
    #     for message in st.session_state.messages_2:
    #         if message["role"] == "assistant":
    #             with st.chat_message(message["role"]):
    #                 st.write(message["content"])


    # 모든 프롬프트 저장
    filename = st.session_state.pv_outputs + st.session_state.session_id+"_all_prompt.json"
    with open(filename, 'w', encoding='utf-8') as f:
        # 모든 데이터를 합친 후 덤프
        all_messages = []
        all_messages.extend([utils.chat_message_to_dict(message) for message in st.session_state["final_tale"]])

        # ### OPTIONAL: zh-cn 한어병음 ###
        # # 한어병음이 있으면 한어병음 추가
        # if "messages_2" in st.session_state:
        #     all_messages.extend([utils.chat_message_to_dict(message) for message in st.session_state["messages_2"]])

        json.dump(all_messages, f, ensure_ascii=False, indent=4)

    st.success("생성 완료")
    st.write("동화 생성이 완료되었습니다. 상호작용을 시작합니다.")


### 마지막 상호작용 부분 ###
# 생성된 동화 trim
trimmed_generated_korean_fairytale = []
for idx in range(len(all_messages)):
    if idx % 2 == 0: # 홀수 페이지
        trimmed_generated_korean_fairytale.append(all_messages[idx]['content'])
trimmed_generated_korean_fairytale = ' '.join(trimmed_generated_korean_fairytale)

# 컨테이너를 사용하여 채팅 영역과 입력 영역을 분리
chat_container = st.container()
input_container = st.container()

# 세션 상태 변수 초기화
if 'interaction_for_child_parent' not in st.session_state:
    st.session_state.interaction_messages = []
    st.session_state.interaction_messages.append({"role" : "system", "content" : 
        f'''
        너는 부모가 아이들에게 이야기를 읽어주며 한국어와 제 2언어인 {st.session_state.select_lang_name}의 언어 이해 능력을 키우고, 부모와의 상호작용을 돕는 챗봇이야. 

        지시 사항:
        1. 질문은 1개만 출력해.
        2. 아이가 스토리와 가족 간의 경험, 자신의 경험, 감정을 연결하도록 유도해.
        3. 아이가 답변하면, 바로 아이가 받은 첫 번째 질문을 자연스럽게 제 2언어로 말하도록 유도해.
        4. 아이의 답변이 유도하기에 충분하지 않다면 다시 질문해.
        5. 아이가 질문을 직접 제 2언어로 말하도록 유도하되, 절대 질문을 제 2언어로 번역해서 제공하면 안돼.

        다음 진행 예시를 참고해서 진행해:
        <진행 예시1>
        - 부모의 선호 요소: 미국, 유아, 한국어, 영어, 날씨에 대한 표현, 풋볼
        - 아이의 선호 요소: 아이스크림, 강아지, 보라색, 블록쌓기, 루피
        - GPT의 질문: 퍼플이 블럭으로 풋볼 경기장을 만들었어! 너는 블럭이나 장난감으로 뭘 만들어 본 적이 있어? 😊
        - 아이의 예상 답변: 나는 블록으로 경찰차를 만들었어.
        - GPT의 답변: 와! 경찰차를 만들었다니 멋지다! 🚔 이번에는 내가 한 말을 영어로 엄마에게 말해볼까? 엄마랑 같이 말해봐도 좋아! 😊
        <진행 예시2>
        - 부모의 선호 요소: 중국, 유아, 한국어, 중국어, 감정 표현, 중추절
        - 아이의 선호 요소: 아이스크림, 고양이, 하늘색, 게임, 또봇
        - GPT의 질문: 재미있는 이야기였어! 민지가 솜이와 함께 중추절을 즐기는 모습이 정말 따뜻했어. 😊 너는 가족과 함께 특별한 날을 어떻게 보내니?
        - 아이의 예상 답변: 함께 맛있는 음식을 먹어.
        - GPT의 답변: 정말 좋겠다! 가족과 함께 먹는 음식은 더 맛있지. 😊 이제 내가 한 질문을 중국어로 엄마에게 물어봐!

        다음의 요소들과 생성된 동화 이야기를 참고해서 위 예시와 유사하게 진행해:
        - 부모의 선호 요소: {st.session_state.parent_prefer}
        - 아이의 선호 요소: {st.session_state.child_prefer}
        - 생성된 동화 이야기: {trimmed_generated_korean_fairytale}
        '''
    })
    st.session_state.interaction_messages.append({
        "role":"assistant", "content":"생성된 동화는 어떠셨나요? 아이에게 한가지 질문을 해도 괜찮을까요?"
    })

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

# # QNA json?
# filename_l = st.session_state.session_id + "_interaction_qna.json"
# with open(st.session_state.pv_outputs + filename_l, 'w', encoding='utf-8') as f:
#     json.dump(interaction_response, f, ensure_ascii=False, indent=4)