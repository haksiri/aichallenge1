# --- 이 코드를 utils.py 파일에 붙여넣으세요 ---
import os
from openai import OpenAI, RateLimitError, AuthenticationError, APIConnectionError, APIError

# --- OpenAI Whisper API 관련 함수 ---
def transcribe_audio_openai(file_path: str, api_key: str) -> str:
    """오디오 파일을 OpenAI Whisper API를 이용해 텍스트로 변환합니다."""
    if not api_key:
        return "오류: OpenAI API 키가 제공되지 않았습니다."
    if not os.path.exists(file_path):
        return f"오류: 오디오 파일을 찾을 수 없습니다 - {file_path}"

    print(f"Whisper 변환 시도: {file_path}") # 진행 상황 확인용 로그
    try:
        client = OpenAI(api_key=api_key)
        with open(file_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file,
              response_format="text"
            )
        print("Whisper 변환 성공") # 진행 상황 확인용 로그
        return transcript_response.strip()

    except RateLimitError:
         return "오류: OpenAI API 요청 한도를 초과했습니다 (Whisper). 잠시 후 다시 시도해주세요."
    except AuthenticationError:
         return "오류: OpenAI API 키가 유효하지 않습니다 (Whisper). 키를 확인해주세요."
    except APIConnectionError:
         return "오류: OpenAI 서버에 연결할 수 없습니다 (Whisper). 네트워크 연결을 확인해주세요."
    except APIError as e:
         print(f"[Whisper] OpenAI API 오류: {e}")
         # API가 반환한 오류 메시지를 포함하여 사용자에게 전달
         error_message = getattr(e, 'message', str(e))
         return f"오류: Whisper API 처리 중 문제가 발생했습니다. {error_message}"
    except Exception as e:
        print(f"[Whisper] 예상치 못한 오류 발생: {e}")
        return f"오류: 음성 변환 중 예상치 못한 문제가 발생했습니다. ({type(e).__name__})"

# --- OpenAI GPT 분석 관련 함수 ---
def analyze_lecture_openai(prompt: str, api_key: str) -> str:
    """주어진 프롬프트를 사용하여 OpenAI API를 통해 강의 내용을 분석합니다."""
    if not api_key:
        return "오류: OpenAI API 키가 제공되지 않았습니다."

    print("GPT 분석 시도...") # 진행 상황 확인용 로그
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview", # 또는 gpt-3.5-turbo 등
            messages=[
                {"role": "system", "content": "You are a helpful assistant skilled in analyzing lecture transcripts and generating educational content based on Korean user requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        analysis_result = response.choices[0].message.content
        print("GPT 분석 성공") # 진행 상황 확인용 로그
        return analysis_result.strip()

    except RateLimitError:
         return "오류: OpenAI API 요청 한도를 초과했습니다 (GPT). 잠시 후 다시 시도해주세요."
    except AuthenticationError:
         return "오류: OpenAI API 키가 유효하지 않습니다 (GPT). 키를 확인해주세요."
    except APIConnectionError:
         return "오류: OpenAI 서버에 연결할 수 없습니다 (GPT). 네트워크 연결을 확인해주세요."
    except APIError as e:
         print(f"[GPT] OpenAI API 오류: {e}")
         error_message = getattr(e, 'message', str(e))
         return f"오류: GPT API 처리 중 문제가 발생했습니다. {error_message}"
    except Exception as e:
        print(f"[GPT] 예상치 못한 오류 발생: {e}")
        return f"오류: AI 분석 중 문제가 발생했습니다. ({type(e).__name__})"

# --- END of utils.py code ---