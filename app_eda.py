import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # --- [수정] 데이터셋 소개를 '지역별 인구 분석'으로 변경 ---
        st.markdown("""
                ---
                **지역별 인구 분석 데이터셋**  
                - 원본 파일: `population_trends.csv`  
                - 설명: 2008년부터 2023년까지 대한민국의 시/도별 연간 인구, 출생아 수, 사망자 수 데이터입니다.  
                - 주요 변수:  
                  - `연도`: 데이터 기준 연도  
                  - `지역`: 전국 및 각 시/도  
                  - `인구`: 총 인구 수  
                  - `출생아수(명)`: 해당 연도 출생아 수  
                  - `사망자수(명)`: 해당 연도 사망자 수
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 EDA 분석")

        # --- [수정] 분석 선택 옵션을 제거하고 '지역별 인구 분석'을 기본으로 실행 ---
        # analysis_choice = st.selectbox(
        #     "분석할 데이터 종류를 선택하세요.",
        #     ("Bike Sharing Demand", "지역별 인구 분석")
        # )
        #
        # # 선택에 따라 다른 분석을 보여주도록 분기
        # if analysis_choice == "Bike Sharing Demand":
        #     self.run_bike_sharing_eda()
        # elif analysis_choice == "지역별 인구 분석":
        #     self.run_population_trends_eda()
        self.run_population_trends_eda() # 인구 분석 함수를 직접 호출

    # --- [수정] Bike Sharing EDA 관련 함수 전체 주석 처리 ---
    """
    def run_bike_sharing_eda(self):
        st.header("🚲 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv", key="bike_uploader")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown(
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 데이터 구조 및 기초 통계 확인  
            2. 결측치/중복치 등 품질 체크  
            3. datetime 특성(연도, 월, 일, 시, 요일) 추출  
            4. 주요 변수 시각화  
            5. 변수 간 상관관계 분석  
            6. 이상치 탐지 및 제거  
            7. 로그 변환을 통한 분포 안정화
            )

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f
            - **train.csv**: 2011–2012년까지의 시간대별 대여 기록  
            - 총 관측치: {df.shape[0]}개  
            - 주요 변수:
              - **datetime**: 날짜와 시간 (YYYY-MM-DD HH:MM:SS)  
              - **season**: 계절 (1: 봄, 2: 여름, 3: 가을, 4: 겨울)  
              - **holiday**: 공휴일 여부 (0: 평일, 1: 공휴일)  
              - **workingday**: 근무일 여부 (0: 주말/공휴일, 1: 근무일)  
              - **weather**: 날씨 상태  
                - 1: 맑음·부분적으로 흐림  
                - 2: 안개·흐림  
                - 3: 가벼운 비/눈  
                - 4: 폭우/폭설 등  
              - **temp**: 실제 기온 (섭씨)  
              - **atemp**: 체감 온도 (섭씨)  
              - **humidity**: 상대 습도 (%)  
              - **windspeed**: 풍속 (정규화된 값)  
              - **casual**: 비등록 사용자 대여 횟수  
              - **registered**: 등록 사용자 대여 횟수  
              - **count**: 전체 대여 횟수 (casual + registered)
            )

            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("2) 기초 통계량 (`df.describe()`)")
            numeric_df = df.select_dtypes(include=[np.number])
            st.dataframe(numeric_df.describe())

            st.subheader("3) 샘플 데이터 (첫 5행)")
            st.dataframe(df.head())

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📥 데이터 로드 & 품질 체크")
            st.subheader("결측값 개수")
            missing = df.isnull().sum()
            st.bar_chart(missing)

            duplicates = df.duplicated().sum()
            st.write(f"- 중복 행 개수: {duplicates}개")

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            st.markdown("`datetime` 컬럼에서 연, 월, 일, 시, 요일 등을 추출합니다.")

            df['year'] = df['datetime'].dt.year
            df['month'] = df['datetime'].dt.month
            df['day'] = df['datetime'].dt.day
            df['hour'] = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek

            st.subheader("추출된 특성 예시")
            st.dataframe(df[['datetime', 'year', 'month', 'day', 'hour',
                             'dayofweek']].head())

            # --- 요일 숫자 → 요일명 매핑 (참고용) ---
            day_map = {
                0: '월요일',
                1: '화요일',
                2: '수요일',
                3: '목요일',
                4: '금요일',
                5: '토요일',
                6: '일요일'
            }
            st.markdown("**(참고) dayofweek 숫자 → 요일**")
            # 중복 제거 후 정렬하여 표시
            mapping_df = pd.DataFrame({
                'dayofweek': list(day_map.keys()),
                'weekday': list(day_map.values())
            })
            st.dataframe(mapping_df, hide_index=True)

        # 5. 시각화
        with tabs[4]:
            st.header("📈 시각화")
            # by 근무일 여부
            st.subheader("근무일 여부별 시간대별 평균 대여량")
            fig1, ax1 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='workingday', data=df,
                          ax=ax1)
            ax1.set_xlabel("Hour");
            ax1.set_ylabel("Average Count")
            st.pyplot(fig1)
            st.markdown(
                "> **해석:** 근무일(1)은 출퇴근 시간(7 ~ 9시, 17 ~ 19시)에 대여량이 급증하는 반면,\n"
                "비근무일(0)은 오후(11 ~ 15시) 시간대에 대여량이 상대적으로 높게 나타납니다."
            )

            # by 요일
            st.subheader("요일별 시간대별 평균 대여량")
            fig2, ax2 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='dayofweek', data=df, ax=ax2)
            ax2.set_xlabel("Hour");
            ax2.set_ylabel("Average Count")
            st.pyplot(fig2)
            st.markdown(
                "> **해석:** 평일(월 ~ 금)은 출퇴근 피크가 두드러지고,\n"
                "주말(토~일)은 오전 중반(10 ~ 14시)에 대여량이 더 고르게 분포하는 경향이 있습니다."
            )

            # by 시즌
            st.subheader("시즌별 시간대별 평균 대여량")
            fig3, ax3 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='season', data=df, ax=ax3)
            ax3.set_xlabel("Hour");
            ax3.set_ylabel("Average Count")
            st.pyplot(fig3)
            st.markdown(
                "> **해석:** 여름(2)과 가을(3)에 전반적으로 대여량이 높고,\n"
                "겨울(4)은 전 시간대에 걸쳐 대여량이 낮게 나타납니다."
            )

            # by 날씨
            st.subheader("날씨 상태별 시간대별 평균 대여량")
            fig4, ax4 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='weather', data=df, ax=ax4)
            ax4.set_xlabel("Hour");
            ax4.set_ylabel("Average Count")
            st.pyplot(fig4)
            st.markdown(
                "> **해석:** 맑음(1)은 전 시간대에서 대여량이 가장 높으며,\n"
                "안개·흐림(2), 가벼운 비/눈(3)에선 다소 감소하고, 심한 기상(4)에서는 크게 떨어집니다."
            )

        # 6. 상관관계 분석
        with tabs[5]:
            st.header("🔗 상관관계 분석")
            # 관심 피처만 선택
            features = ['temp', 'atemp', 'casual', 'registered', 'humidity',
                        'windspeed', 'count']
            corr_df = df[features].corr()

            # 상관계수 테이블 출력
            st.subheader("📊 피처 간 상관계수")
            st.dataframe(corr_df)

            # 히트맵 시각화
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            ax.set_xlabel("")  # 축 이름 제거
            ax.set_ylabel("")
            st.pyplot(fig)
            st.markdown(
                "> **해석:**\n"
                "- `count`는 `registered` (r≈0.99) 및 `casual` (r≈0.67)와 강한 양의 상관관계를 보입니다.\n"
                "- `temp`·`atemp`와 `count`는 중간 정도의 양의 상관관계(r≈0.4~0.5)를 나타내며, 기온이 높을수록 대여량이 증가함을 시사합니다.\n"
                "- `humidity`와 `windspeed`는 약한 음의 상관관계(r≈-0.2~-0.3)를 보여, 습도·풍속이 높을수록 대여량이 다소 감소합니다."
            )

        # 7. 이상치 제거
        with tabs[6]:
            st.header("🚫 이상치 제거")
            # 평균·표준편차 계산
            mean_count = df['count'].mean()
            std_count = df['count'].std()
            # 상한치: 평균 + 3*표준편차
            upper = mean_count + 3 * std_count

            st.markdown(f
                        - **평균(count)**: {mean_count:.2f}  
                        - **표준편차(count)**: {std_count:.2f}  
                        - **이상치 기준**: `count` > 평균 + 3×표준편차 = {upper:.2f}  
                          (통계학의 68-95-99.7 법칙(Empirical rule)에 따라 평균에서 3σ를 벗어나는 관측치는 전체의 약 0.3%로 극단치로 간주)
                        )
            df_no = df[df['count'] <= upper]
            st.write(f"- 이상치 제거 전: {df.shape[0]}개, 제거 후: {df_no.shape[0]}개")

        # 8. 로그 변환
        with tabs[7]:
            st.header("🔄 로그 변환")
            st.markdown(
                **로그 변환 맥락**  
                - `count` 변수는 오른쪽으로 크게 치우친 분포(skewed distribution)를 가지고 있어,  
                  통계 분석 및 모델링 시 정규성 가정이 어렵습니다.  
                - 따라서 `Log(Count + 1)` 변환을 통해 분포의 왜도를 줄이고,  
                  중앙값 주변으로 데이터를 모아 해석력을 높입니다.
                )

            # 변환 전·후 분포 비교
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))

            # 원본 분포
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Original Count Distribution")
            axes[0].set_xlabel("Count")
            axes[0].set_ylabel("Frequency")

            # 로그 변환 분포
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            axes[1].set_xlabel("Log(Count + 1)")
            axes[1].set_ylabel("Frequency")

            st.pyplot(fig)

            st.markdown(
                > **그래프 해석:**  
                > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                )
    """

    def run_population_trends_eda(self):
        st.header("📈 지역별 인구 트렌드 분석")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv", key="population_uploader")

        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return
        
        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)
        cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
        for col in cols_to_numeric:
            df[col] = pd.to_numeric(df[col])
            
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화", "심층 분석(추가)"
        ])

        with tab1:
            st.subheader("1. 데이터 전처리 및 기본 정보")
            st.write("✅ '세종' 지역을 포함한 모든 데이터의 결측치('-')를 0으로 치환했습니다.")
            st.write(f"✅ 다음 컬럼들을 숫자(numeric) 타입으로 변환했습니다: {', '.join(cols_to_numeric)}")
            st.markdown("---")
            st.subheader("데이터 요약 통계 (`df.describe()`)")
            st.dataframe(df.describe())

            st.subheader("데이터프레임 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("샘플 데이터 (전처리 후)")
            st.dataframe(df.head())
        
        with tab2:
            st.subheader("2. 연도별 전체 인구 추이 (전국)")
            korea_df = df[df['지역'] == '전국'].copy()
            recent_3_years = korea_df.nlargest(3, '연도')
            avg_births = recent_3_years['출생아수(명)'].mean()
            avg_deaths = recent_3_years['사망자수(명)'].mean()
            avg_change = avg_births - avg_deaths
            last_year_data = korea_df.nlargest(1, '연도')
            last_year = last_year_data['연도'].iloc[0]
            last_population = last_year_data['인구'].iloc[0]
            predictions = []
            current_pop = last_population
            for year in range(last_year + 1, 2036):
                current_pop += avg_change
                predictions.append({'연도': year, '인구': current_pop})
            
            pred_df = pd.DataFrame(predictions)

            fig, ax = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=korea_df, x='연도', y='인구', ax=ax, marker='o', label='Actual Population')
            sns.lineplot(data=pred_df, x='연도', y='인구', ax=ax, marker='o', linestyle='--', color='red', label='Predicted Population (to 2035)')
            ax.set_title('Total Population Trend and Prediction in Korea')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.grid(True)
            ax.legend()
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            st.pyplot(fig)

            st.markdown(f"""
            #### 인구 예측 요약
            - **예측 기준**: 최근 3년간('전국' 기준) 연평균 출생아 수와 사망자 수의 차이를 기반으로 함
              - 연평균 출생아 수: `{int(avg_births):,}` 명
              - 연평균 사망자 수: `{int(avg_deaths):,}` 명
              - 연평균 인구 변화량: `{int(avg_change):,}` 명
            - **가장 최근 인구 ({last_year}년)**: `{int(last_population):,}` 명
            - **2035년 예측 인구**: `{int(pred_df.iloc[-1]['인구']):,}` 명
            """)

        with tab3:
            st.subheader("3. 지역별 인구 변화 (최근 5년)")
            df_local = df[df['지역'] != '전국'].copy()
            end_year = df_local['연도'].max()
            start_year = end_year - 5
            pop_start = df_local[df_local['연도'] == start_year][['지역', '인구']]
            pop_end = df_local[df_local['연도'] == end_year][['지역', '인구']]
            merged_df = pd.merge(pop_start, pop_end, on='지역', suffixes=(f'_{start_year}', f'_{end_year}'))
            merged_df['change'] = merged_df[f'인구_{end_year}'] - merged_df[f'인구_{start_year}']
            merged_df['change_rate'] = (merged_df['change'] / merged_df[f'인구_{start_year}']) * 100
            merged_df['Region_EN'] = merged_df['지역'].map(region_map)

            st.write(f"#### Population Change ({start_year} vs {end_year})")
            sorted_change = merged_df.sort_values('change', ascending=False)
            sorted_change['change_k'] = sorted_change['change'] / 1000
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=sorted_change, x='change_k', y='Region_EN', ax=ax1, palette='viridis')
            ax1.set_title(f'Population Change from {start_year} to {end_year}')
            ax1.set_xlabel('Change (in thousands)')
            ax1.set_ylabel('Region')
            for p in ax1.patches:
                width = p.get_width()
                y = p.get_y() + p.get_height() / 2
                ax1.text(width + (5 if width > 0 else -5), y, f'{width:,.1f}K', ha=('left' if width > 0 else 'right'), va='center')
            st.pyplot(fig1)

            st.write(f"#### Population Change Rate ({start_year} vs {end_year})")
            sorted_rate = merged_df.sort_values('change_rate', ascending=False)
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=sorted_rate, x='change_rate', y='Region_EN', ax=ax2, palette='plasma')
            ax2.set_title(f'Population Change Rate from {start_year} to {end_year}')
            ax2.set_xlabel('Change Rate (%)')
            ax2.set_ylabel('Region')
            for p in ax2.patches:
                width = p.get_width()
                y = p.get_y() + p.get_height() / 2
                ax2.text(width + (0.1 if width > 0 else -0.1), y, f'{width:.2f}%', ha=('left' if width > 0 else 'right'), va='center')
            st.pyplot(fig2)

            st.markdown("""
            #### 그래프 해설
            - **Population Change (절대 변화량)**: 최근 5년간 실제 인구가 얼마나 변했는지를 보여줍니다.
              - **경기, 인천, 세종, 충남, 제주** 지역은 인구가 크게 증가했으며, 특히 **경기도**의 증가폭이 가장 두드러집니다.
              - 반면 **서울, 부산, 대구** 등 주요 대도시는 인구가 감소하는 경향을 보입니다.
            - **Population Change Rate (상대 변화율)**: 5년 전 인구 대비 변화율을 나타냅니다.
              - **세종시**는 기존 인구 규모가 작았기 때문에, 절대적인 증가량은 경기도보다 작지만 변화율 측면에서는 압도적으로 높은 수치를 기록했습니다.
              - 이는 신도시 개발과 같은 급격한 인구 유입이 있었음을 시사합니다.
            """)
        
        with tab4:
            st.subheader("4. 연도별 인구 증감 Top 100")
            df_local_sorted = df[df['지역'] != '전국'].sort_values(by=['지역', '연도'])
            df_local_sorted['증감'] = df_local_sorted.groupby('지역')['인구'].diff().fillna(0)
            top_100_changes = df_local_sorted.reindex(df_local_sorted['증감'].abs().sort_values(ascending=False).index).head(100)
            top_100_display = top_100_changes[['연도', '지역', '인구', '증감']].copy()
            top_100_display.rename(columns={'연도': 'Year', '지역': 'Region', '인구': 'Population', '증감': 'Change'}, inplace=True)
            
            st.dataframe(
                top_100_display.style.format({
                    'Population': '{:,.0f}',
                    'Change': '{:,.0f}'
                }).background_gradient(
                    cmap=sns.diverging_palette(10, 240, as_cmap=True), 
                    subset=['Change']
                ),
                hide_index=True,
                width=600 
            )
            st.markdown("""
            #### 테이블 해설
            - 위 표는 모든 지역의 각 연도별 인구 증감(전년 대비)을 계산하여, **증가량이 크거나 감소량이 큰 순서대로 100개**의 사례를 보여줍니다.
            - **'Change'** 열의 배경색이 **파란색**에 가까울수록 인구가 크게 증가했음을 의미하며, **빨간색**에 가까울수록 크게 감소했음을 나타냅니다.
            - 이 표를 통해 어느 지역에서, 어느 연도에 인구 변동이 가장 활발했는지 직관적으로 파악할 수 있습니다.
            """)
        
        with tab5:
            st.subheader("5. 지역별 인구 추이 시각화")
            df_local = df[df['지역'] != '전국'].copy()
            df_local['Region_EN'] = df_local['지역'].map(region_map)
            pivot_df = df_local.pivot_table(index='연도', columns='Region_EN', values='인구', aggfunc='sum')
            pivot_df.fillna(0, inplace=True)

            fig, ax = plt.subplots(figsize=(14, 8))
            colors = plt.cm.get_cmap('tab20', len(pivot_df.columns))
            ax.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns, colors=colors.colors)
            ax.set_title('Population Trend by Region (Stacked Area Chart)')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax.legend(title='Regions', loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.)
            plt.tight_layout(rect=[0, 0, 0.85, 1])
            st.pyplot(fig)
            
            st.markdown("""
            #### 그래프 해설
            - 이 그래프는 각 지역의 연도별 인구수를 누적하여 보여줍니다. 전체 높이는 '전국'을 제외한 모든 지역의 인구 합계를 나타냅니다.
            - 각 색상 영역의 **두께**가 해당 지역의 인구 규모를 의미합니다.
            - **경기(Gyeonggi)** 지역을 나타내는 영역(보통 가장 큰 영역 중 하나)이 시간이 지남에 따라 꾸준히 두꺼워지는 것을 통해 지속적인 인구 증가를 확인할 수 있습니다.
            - 반면 **서울(Seoul)** 영역은 점차 얇아지는 모습을 보여 인구 감소 추세를 시각적으로 파악할 수 있습니다.
            - **세종(Sejong)** 지역에서는 2012년부터 나타나며 가파르게 성장하는 작은 영역으로 표시됩니다.
            """)

        # --- [신규 추가] 인구 동태 분석 탭 ---
        with tab6:
            st.subheader("6. 지역별 인구 동태 심층 분석")
            
            # 사용자 선택을 위한 지역 목록 (전국 제외)
            local_regions = df[df['지역'] != '전국']['지역'].unique()
            selected_region = st.selectbox("분석할 지역을 선택하세요.", local_regions, key="dynamic_analysis_region")

            # 선택된 지역 데이터 필터링
            region_df = df[df['지역'] == selected_region].sort_values('연도').copy()
            
            # '자연증감' 컬럼을 여기서 생성
            region_df['자연증감'] = region_df['출생아수(명)'] - region_df['사망자수(명)']

            st.write(f"#### {selected_region}의 출생, 사망 및 자연증감 추이")

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(region_df['연도'], region_df['출생아수(명)'], marker='o', color='green', label='Births')
            ax.plot(region_df['연도'], region_df['사망자수(명)'], marker='o', color='red', label='Deaths')
            ax.bar(region_df['연도'], region_df['자연증감'], color='grey', alpha=0.5, label='Natural Increase')
            ax.axhline(0, color='black', linestyle='--', linewidth=1)
            ax.set_title(f'Births, Deaths, and Natural Increase in {region_map.get(selected_region, selected_region)}')
            ax.set_xlabel('Year')
            ax.set_ylabel('Number of People')
            ax.legend()
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            st.pyplot(fig)

            dead_cross_year = region_df[region_df['자연증감'] < 0]['연도'].min()
            if pd.notna(dead_cross_year):
                st.error(f"**데드크로스 발생**: {selected_region}은(는) **{int(dead_cross_year)}년**부터 사망자 수가 출생아 수를 넘어서는 '인구 데드크로스' 현상이 시작되었습니다.")
            else:
                st.success(f"**데드크로스 미발생**: {selected_region}은(는) 아직 출생아 수가 사망자 수보다 많습니다.")

            st.markdown("""
            #### 그래프 및 분석 해설
            - **출생아 수(Births)**와 **사망자 수(Deaths)** 추이를 통해 인구 변동의 핵심 요인을 파악할 수 있습니다.
            - **자연 증감(Natural Increase)**은 `출생아 수 - 사망자 수`로, 양수(+)이면 인구가 자연적으로 증가하고, 음수(-)이면 자연적으로 감소함을 의미합니다.
            - 두 선이 교차하고 자연 증감 막대가 0 아래로 내려가는 시점이 바로 **데드크로스**가 발생한 해입니다.
            ---
            """)

            st.write(f"#### 최신 연도({df['연도'].max()}) 기준, 모든 지역의 자연증감 비교")
            latest_year_df = df[df['연도'] == df['연도'].max()].copy()
            
            latest_year_df['자연증감'] = latest_year_df['출생아수(명)'] - latest_year_df['사망자수(명)']
            latest_local_df = latest_year_df[latest_year_df['지역'] != '전국'].sort_values('자연증감', ascending=False)
            
            # --- [수정] 그래프를 그리기 전에 지역명을 영문으로 변환 ---
            latest_local_df['Region_EN'] = latest_local_df['지역'].map(region_map)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            palette = sns.diverging_palette(10, 240, n=2)
            # --- [수정] y축에 한글 '지역' 대신 영문 'Region_EN'을 사용 ---
            sns.barplot(data=latest_local_df, x='자연증감', y='Region_EN', ax=ax2, 
                        palette=[palette[1] if x > 0 else palette[0] for x in latest_local_df['자연증감']])
            ax2.set_title(f"Natural Population Increase by Region ({df['연도'].max()})")
            ax2.set_xlabel("Natural Increase (Births - Deaths)")
            ax2.set_ylabel("Region") # Y축 레이블도 영문으로 유지
            st.pyplot(fig2)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()