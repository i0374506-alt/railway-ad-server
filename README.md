# Screen Capture Defender - 광고 서버

Railway에서 호스팅되는 광고 API 서버입니다.

## 🚀 Railway 배포 방법

### 1. Railway 계정 생성
- https://railway.app 접속
- GitHub 계정으로 로그인

### 2. 새 프로젝트 생성
- Dashboard에서 "New Project" 클릭
- "Deploy from GitHub repo" 선택
- 이 저장소 연결

### 3. 환경변수 설정 (선택)
- Variables 탭에서 추가:
  - `ADMIN_USER`: 관리자 아이디 (기본: admin)
  - `ADMIN_PASS`: 관리자 비밀번호 (기본: 1234)

### 4. 배포 완료!
- 자동으로 도메인 생성됨
- 예: `https://your-app.up.railway.app`

## 📡 API 엔드포인트

| URL | 설명 |
|-----|------|
| `/` | 서버 상태 |
| `/admin` | 관리자 페이지 |
| `/api/ad-config.json` | 광고 설정 API |
| `/uploads/<파일명>` | 업로드된 이미지 |

## ⚙️ 관리자 페이지

- URL: `https://your-app.up.railway.app/admin`
- 기본 로그인: admin / 1234

### 기능
- ✅ 이미지 직접 업로드
- ✅ 클릭 링크 설정
- ✅ 배너 활성화/비활성화
- ✅ 클릭 통계
- ✅ 실시간 적용

## 💰 요금

Railway 무료 플랜: 월 $5 크레딧 제공
- 이 앱은 거의 리소스를 사용하지 않아 무료로 운영 가능
