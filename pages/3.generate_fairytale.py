import streamlit as st
import openai, os, json, random
from dotenv import load_dotenv
import utils
from PIL import Image

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


### 동화 작성 부분 ###
# 첫번째 동화 생성
if 'first_tale' not in st.session_state:
    with st.spinner("동화 만들 재료 수집 하는 중..."):
        llm_1 = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 다문화 가정 아동들의 이중 언어 발달을 돕기 위한 동화책 작가입니다."},
                {"role":"user","content": f'''
                다음 요소들을 기억해: 부모의 선호 요소는 {st.session_state.parent_prefer} & 아동의 선호 요소는 {st.session_state.child_prefer}

                그리고 다음 7가지 조건으로 동화를 구성해.
                1. 아동의 선호 요소를 넣어
                2. ‘표현’ 을 학습할 수 있게 동화 안에 넣어
                3. 부모의 ‘출신 국가’ 를 동화의 사건, 배경, 등장인물 등에 적용해
                4. ‘문화’ 에 대한 설명을 자연스럽게 넣어
                5. 주어진 요소들을 이름으로 사용하면 안돼
                6. 등장인물들은 모두 이름을 가지고 있어야 해
                7. 아동의 표현력이 향상할 수 있도록 동화를 만들어
            
                동화의 분량은 다음 조건을 지켜서 생성해: 총 6페이지, 각 페이지 당 글자 수 30자 이상 70자 이하로 만들어.
                위의 조건들을 모두 포함하여 한국어로 동화를 생성해. 그리고 모든 내용은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성되게 만들어.
                
                만약 부모의 선호 요소가 캐나다, 한국어, 영어, 날씨에 대한 표현, 아이스 하키 이고, 
                아동의 선호 요소가 젤리, 고양이, 하늘색, 숨바꼭질, 루피 라고 한다면 다음 <예시>처럼 동화를 생성해.
                <예시>
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
            
                3. 길이: 총 12페이지 (한국어 6페이지, 제 2언어 6페이지)
            
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

    # ### OPTIONAL: cn(zh-cn) 한어병음 ###
    # # 언어가 중국어일 때 한어 병음 추가
    # if st.session_state.select_language == 'cn':
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
        "kids illustration, oil pastel in a dreamy color palette",
        "kids illustration, colored pencil in a cute and adorable style",
        "adorable storybook illustration with large pastel, a color pencil sketch inspired by Edwin Landseer",
        "a storybook illustration by Aesop's Fables",
        "a storybook-style illustration for children",
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

                선호 요소 예시: 캐나다, 한국어, 영어, 날씨에 대한 표현, 아이스 하키 & 젤리, 고양이, 하늘색, 숨바꼭질, 루피
                예시 형식:
                페이지 1: 파란 하늘이 맑게 펼쳐진 아침이에요. 오늘은 날씨가 좋아서 루피가 기분이 좋아졌어요.,
                페이지 3: "오늘은 숨바꼭질을 해야겠다!" 고양이 인형을 꼭 안고 있는 루피는 놀이를 하고 싶다고 이야기했어요.,
                페이지 5: 루피는 젤리와 함께 집 앞 공원으로 나갔어요. 공원에는 아이들이 놀고 있었어요.",
                페이지 9: 공원의 한쪽에서는 피자를 먹고 있는 가족들이 있었어요. "피자 냄새가 좋아!" 루피는 냄새를 맡으며 말했어요
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
                주어진 스토리에서 모든 캐릭터를 추출하고 캐릭터가 무엇인지 영어로 출력하세요.
                만일 Sam 이라는 다람쥐 캐릭터라면 ‘Sam the squirrel’ 로 출력하세요. 그리고 캐릭터의 생김새를 출력하세요.
                만일 캐릭터가 사람이라면 캐릭터의 이목구비, 헤어, 의상을 형식처럼 출력하세요.
                그리고 모든 설명은 OpenAI의 콘텐츠 안전 정책에 위반하지 않는 단어들로만 구성하세요.

                형식:
                페이지 1: (Subject) Loopy the child, (Appearance) Small size, round face, big round eyes, (Hair) Soft curls in light brown, (Clothes) Bright pastel blue shirt
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
                페이지 1: (Feeling) Happy, (Action) Watching the flowers, (Background) Old tree, (Adjective) Luscious, (Environment) In the forest
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
                페이지 1: (Subject) Loopy the child, (Appearance) Small size, round face, big round eyes, (Hair) Soft curls in light brown (Clothes) Bright pastel blue shirt, (Feeling) Happy (Action) Watching the flowers, (Background) Old tree, (Adjective) Luscious, (Environment) In the forest,
                페이지 3: (Subject) Crong the playful bunny, (Appearance) Fluffy ears, small button nose, big smile, (Color) Soft cream white, (Clothes) Green bow tie, (Feeling) Curious, (Action) Holding a strawberry, (Background) Grassy hill, (Adjective) Gentle slope, (Environment) In a sunny meadow
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
if 'ref_prompt' not in st.session_state:
    ref_prompt = utils.sanitize_prompt(st.session_state.prompt4)
    st.session_state.ref_prompt = ref_prompt


#이미지와 넘버 매치
if 'dict_imgs' not in st.session_state:
    urls_list = utils.generate_image(
        word = st.session_state.ref_prompt,
        client = client,
        setting = st.session_state.image_style,
        model = "dall-e-3"
    )
    num_list = st.session_state.img_num
    st.session_state.dict_imgs = dict(zip(num_list, urls_list))


### 동화 최종 생성 부분 ###
if 'initiate_final_tale_generation' not in st.session_state:
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
                                resized_image = Image.open(st.session_state.dict_imgs[page_number])
                                resized_image = resized_image.resize((512, 512))
                                st.image(resized_image)
                                
        # ### OPTIONAL: cn(zh-cn) 한어병음 ###
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

            # ### OPTIONAL: cn(zh-cn) 한어병음 ###
            # # 한어병음이 있으면 한어병음 추가
            # if "messages_2" in st.session_state:
            #     all_messages.extend([utils.chat_message_to_dict(message) for message in st.session_state["messages_2"]])

            json.dump(all_messages, f, ensure_ascii=False, indent=4)

        st.success("생성 완료")
        st.session_state.initiate_final_tale_generation = True
        st.write("상호작용을 시작합니다. 다음 페이지에서도 동화를 계속 보실 수 있습니다. 다음 버튼을 눌러주세요.")
        st.page_link("pages/4.interaction.py", label="상호작용", icon="4️⃣")
