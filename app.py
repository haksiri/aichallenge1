# --- 이 코드를 app.py 파일에 붙여넣으세요 ---
import streamlit as st
import os
# utils.py 에서 함수들을 가져옵니다.
from utils import transcribe_audio_openai, analyze_lecture_openai

# --- 페이지 설정 ---
st.set_page_config(page_title="강의 분석 AI 도우미", layout="wide")

# --- API 키 로드 (Streamlit Secrets 사용) ---
# 이 부분은 Streamlit Cloud에 배포했을 때 secrets 설정에서 키를 읽어옵니다.
# 로컬 테스트 시에는 작동하지 않으므로, 아래 "로컬 테스트 방법" 참고
openai_api_key = "" # 기본값 초기화
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    if not openai_api_key: # 키 값이 비어있는 경우 처리
         st.warning("Streamlit Secrets에 OpenAI API 키가 설정되지 않았거나 비어있습니다.", icon="⚠️")
except (FileNotFoundError, KeyError):
    # 로컬 실행 시 secrets 파일이 없으므로 이 경고가 표시될 수 있습니다.
    st.warning("Streamlit Secrets 설정을 찾을 수 없습니다. 로컬 테스트 시에는 API 키를 직접 입력하거나 환경 변수를 사용해야 할 수 있습니다. 배포 시에는 Secrets를 설정해주세요.", icon="⚠️")

# --- 앱 제목 및 설명 ---
st.title("🎓 강의 분석 AI 도우미 (OpenAI Whisper & GPT)")
st.write("음성 파일을 업로드하면 OpenAI가 내용을 분석하고 학습 자료를 만들어줍니다.")
st.markdown("---")

# --- 사용자 입력 섹션 ---
col1, col2 = st.columns([2, 1]) # 화면 분할

with col1:
    st.subheader("1. 음성 파일 업로드")
    uploaded_file = st.file_uploader(
        "분석할 음성 파일을 올려주세요 (mp3, wav, m4a, ogg, flac 등 Whisper 지원 형식)",
        type=['mp3', 'wav', 'm4a', 'ogg', 'flac', 'mpga', 'mpeg', 'webm']
    )
    # API 키 입력 (로컬 테스트용 - 배포 시에는 secrets 사용)
    if not openai_api_key: # secrets에 키가 없을 때만 입력 필드 표시
         st.info("OpenAI API 키를 Secrets에 설정하지 않은 경우, 아래에 임시로 입력하여 로컬에서 테스트할 수 있습니다. (배포 전에는 제거 필요)")
         openai_api_key_input = st.text_input("OpenAI API 키 (sk-...)", type="password")
         if openai_api_key_input:
             openai_api_key = openai_api_key_input # 입력받은 키 사용

with col2:
    st.subheader("2. 분석 옵션 설정")
    learning_level = st.selectbox(
        "대상 학습 수준",
        ["초등학생", "중학생", "고등학생", "대학생(교양)", "대학생(전공)", "전문가"],
        index=3
    )
    lecture_field = st.text_input("강의 분야", placeholder="예: 파이썬 머신러닝")

# --- 분석 실행 버튼 ---
st.markdown("---")
analyze_button = st.button("✨ AI 분석 시작하기", type="primary", use_container_width=True, disabled=(not openai_api_key)) # API 키 없으면 비활성화

if not openai_api_key and analyze_button:
    st.error("OpenAI API 키가 필요합니다. Streamlit Secrets를 설정하거나 위 입력란에 키를 입력해주세요.")

# --- 결과 출력 섹션 ---
if analyze_button and uploaded_file is not None and openai_api_key:
    # 1. 임시 파일 저장
    temp_dir = "temp_audio"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    base_name = os.path.basename(uploaded_file.name)
    file_name_safe = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in base_name)
    temp_file_path = os.path.join(temp_dir, file_name_safe)

    transcript = "" # 초기화
    analysis_result = "" # 초기화

    try:
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"'{uploaded_file.name}' 파일 업로드 완료 ({uploaded_file.size / 1024 / 1024:.2f} MB).")

        # 2. OpenAI Whisper STT 실행
        with st.spinner("🔊 OpenAI Whisper로 음성을 텍스트로 변환 중... (파일 크기에 따라 몇 분 정도 소요될 수 있습니다)"):
            transcript = transcribe_audio_openai(temp_file_path, openai_api_key)

        if transcript.startswith("오류:"):
            st.error(f"STT 변환 실패: {transcript}")
        else:
            st.success("✅ 텍스트 변환 완료!")
            with st.expander("📝 음성 변환 결과 보기 (클릭)", expanded=False):
                 st.text_area("변환된 텍스트:", transcript, height=250)
            st.markdown("---")

            # 3. OpenAI GPT 분석 실행
            with st.spinner("🧠 OpenAI GPT 모델로 내용 분석 및 학습 자료 생성 중..."):
                # 상세 프롬프트 구성
                prompt = f"""
                당신은 한국어로 소통하는 매우 유능한 교육 콘텐츠 전문가입니다. 주어진 강의 내용을 바탕으로 다음 요청사항을 명확하고 상세하게, 지정된 학습 수준에 맞춰 한국어로 작성해주세요.

                **강의 정보:**
                * **강의 분야:** {lecture_field if lecture_field else "지정되지 않음"}
                * **대상 학습 수준:** {learning_level}

                **원본 강의 텍스트:**
                ```
                {transcript}
                ```

                **요청 사항:**

                1.  **핵심 요약 (200자 내외):** 강의의 가장 중요한 내용을 {learning_level} 수준에 맞춰 간결하게 요약해주세요. 핵심 메시지가 잘 드러나야 합니다.

                2.  **주요 개념 정리 (3가지):** 강의에서 등장한 핵심 개념이나 용어 3가지를 선정하여, 각각 {learning_level} 학생이 이해하기 쉽도록 명확하고 친절하게 설명해주세요. 필요하다면 예시를 들어주세요.

                3.  **복습 퀴즈 (객관식 3문제):** 강의 내용을 잘 이해했는지 확인할 수 있는 객관식 문제 3개를 만들어주세요. 각 문제에는 4개의 보기와 정답 표시가 있어야 하며, {learning_level} 수준에 적합해야 합니다.

                **출력 형식:**
                결과는 아래와 같이 명확한 제목과 함께 Markdown 형식을 사용하여 가독성 좋게 작성해주세요.

                ---
                ### 💡 핵심 요약
                [여기에 요약 내용 작성]

                ---
                ### 🔑 주요 개념 정리
                **1. [개념1]:** [개념1 설명]
                **2. [개념2]:** [개념2 설명]
                **3. [개념3]:** [개념3 설명]

                ---
                ### ❓ 복습 퀴즈
                **문제 1:** [문제 내용]
                (1) [보기1] (2) [보기2] (3) [보기3] (4) [보기4]
                **정답:** (번호)

                **문제 2:** [문제 내용]
                (1) [보기1] (2) [보기2] (3) [보기3] (4) [보기4]
                **정답:** (번호)

                **문제 3:** [문제 내용]
                (1) [보기1] (2) [보기2] (3) [보기3] (4) [보기4]
                **정답:** (번호)
                ---
                """
                analysis_result = analyze_lecture_openai(prompt, openai_api_key)

            if analysis_result.startswith("오류:"):
                st.error(f"AI 분석 실패: {analysis_result}")
            else:
                st.success("✅ AI 분석 및 학습 자료 생성 완료!")
                st.subheader("📊 AI 분석 결과")
                st.markdown(analysis_result) # 마크다운으로 결과 표시

    except Exception as e:
        st.error(f"처리 중 예상치 못한 오류 발생: {e}")
    finally:
        # 4. 임시 파일 삭제 (오류 발생 여부와 관계없이 시도)
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"임시 파일 삭제 완료: {temp_file_path}") # 확인용 로그
            except Exception as e_del:
                 st.warning(f"임시 파일 삭제 중 오류 발생: {e_del}")

elif analyze_button and uploaded_file is None:
    st.warning("⚠️ 분석을 시작하기 전에 음성 파일을 업로드해주세요.")

# --- END of app.py code ---
