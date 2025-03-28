import sys
import time
import os
import urllib.request
import logging
import re
from PyQt5.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from sqlalchemy.orm import sessionmaker
from models import Video, Page, PageVideo, Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('page.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.Page")

class VideoPlayer(QFrame):
    finished = pyqtSignal()
    
    def __init__(self, order, url, title, parent=None):
        super().__init__(parent)
        self.order = order
        self.url = url
        self.title = title
        self.video_id = self.extract_video_id(url)
        self.parent = parent
        self.is_zoomed = False
        self.is_playing = False
        self.init_ui()
        self.load_thumbnail()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logger.info(f"비디오 플레이어 초기화: 순서={order}, 제목={title}, 비디오ID={self.video_id}")
        
    def init_ui(self):
        # 기본 스타일 설정 - 흰색 배경
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
                border: none;
            }
        """)
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 미디어 컨테이너
        self.media_container = QFrame()
        self.media_container.setStyleSheet("background-color: white;")
        media_layout = QVBoxLayout(self.media_container)
        media_layout.setContentsMargins(0, 0, 0, 0)
        media_layout.setSpacing(0)
        
        # 썸네일 이미지 레이블
        self.thumbnail_label = QLabel(self)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            background-color: white;
            border: none;
        """)
        self.thumbnail_label.setMinimumHeight(200)
        media_layout.addWidget(self.thumbnail_label)
        
        # 웹 엔진 뷰 (실제 비디오 플레이어)
        self.web_view = QWebEngineView()
        self.web_view.page().settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        self.web_view.setStyleSheet("""
            background-color: white;
            border: none;
        """)
        self.web_view.hide()  # 초기에는 썸네일만 표시
        media_layout.addWidget(self.web_view)
        
        layout.addWidget(self.media_container, 1)
        
        # 오른쪽 상단에 시간 표시 (영상 길이 또는 남은 시간)
        self.duration_label = QLabel("15")
        self.duration_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.duration_label.setStyleSheet("""
            color: #333; 
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            padding: 3px;
            margin: 5px;
        """)
        self.duration_label.setFixedSize(30, 30)
        
        # 레이블을 미디어 컨테이너 위에 배치
        self.duration_label.setParent(self.media_container)
        self.duration_label.move(self.media_container.width() - 35, 5)
        
    def extract_video_id(self, url):
        if not url:
            logger.warning("URL이 제공되지 않았습니다.")
            return None
            
        # 유튜브 URL 패턴
        patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\s]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^\?\s]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^\?\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                logger.info(f"비디오 ID 추출 성공: {match.group(1)}")
                return match.group(1)
        
        logger.warning(f"URL에서 비디오 ID를 찾을 수 없습니다: {url}")
        return None
        
    def load_thumbnail(self):
        if not self.video_id:
            logger.warning("비디오 ID가 없어 썸네일을 로드할 수 없습니다.")
            self.thumbnail_label.setText("썸네일 없음")
            return
        
        # 캐시 디렉토리 확인/생성
        cache_dir = os.path.join(os.path.expanduser('~'), '.dreambody_cache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # 썸네일 파일 경로
        thumbnail_path = os.path.join(cache_dir, f"{self.video_id}.jpg")
        
        # 이미 다운로드된 썸네일이 있는지 확인
        if os.path.exists(thumbnail_path):
            logger.info(f"캐시된 썸네일 사용: {thumbnail_path}")
            self.display_thumbnail(thumbnail_path)
            return
            
        # 썸네일 URL 생성 및 다운로드
        thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/mqdefault.jpg"
        
        try:
            logger.info(f"썸네일 다운로드 시작: {thumbnail_url}")
            urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
            logger.info(f"썸네일 다운로드 완료: {thumbnail_path}")
            self.display_thumbnail(thumbnail_path)
        except Exception as e:
            logger.error(f"썸네일 다운로드 실패: {str(e)}")
            self.thumbnail_label.setText("썸네일 로드 실패")
    
    def display_thumbnail(self, path):
        try:
            pixmap = QPixmap(path)
            
            # 썸네일 레이블 크기에 맞게 조정
            pixmap = pixmap.scaled(
                self.thumbnail_label.width(), 
                self.thumbnail_label.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.thumbnail_label.setPixmap(pixmap)
            logger.info("썸네일 표시 완료")
        except Exception as e:
            logger.error(f"썸네일 표시 실패: {str(e)}")
            self.thumbnail_label.setText("썸네일 표시 실패")
    
    def load_video(self):
        if not self.video_id:
            logger.warning("비디오 ID가 없어 영상을 로드할 수 없습니다.")
            return False
            
        # 임베드 HTML 생성
        embed_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ margin: 0; padding: 0; background-color: white; overflow: hidden; }}
                .container {{ width: 100%; height: 100vh; display: flex; justify-content: center; align-items: center; }}
                iframe {{ width: 100%; height: 100%; border: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <iframe
                    src="https://www.youtube.com/embed/{self.video_id}?autoplay=1&controls=1&modestbranding=1&rel=0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
        </body>
        </html>
        """
        
        # 웹 뷰에 HTML 로드
        self.web_view.setHtml(embed_html)
        logger.info(f"비디오 {self.order+1} 로드됨: ID={self.video_id}")
        return True
        
    def toggle_play(self):
        if not self.is_playing:
            # 비디오 재생 시작
            if self.load_video():
                self.thumbnail_label.hide()
                self.web_view.show()
                self.is_playing = True
                logger.info(f"비디오 {self.order+1} 재생 시작")
        else:
            # 비디오 정지
            self.web_view.hide()
            self.thumbnail_label.show()
            self.is_playing = False
            logger.info(f"비디오 {self.order+1} 재생 정지")
        
    def set_volume(self, volume):
        # 볼륨 설정 (실제 비디오 로드 시 필요)
        self.volume = volume
        logger.info(f"볼륨 설정: {volume}")
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 크기가 변경되면 썸네일 다시 조정 - 캐시 활용
        if hasattr(self, 'thumbnail_label') and hasattr(self.thumbnail_label, 'pixmap') and self.thumbnail_label.pixmap() and self.video_id:
            thumbnail_path = os.path.join(os.path.expanduser('~'), '.dreambody_cache', f"{self.video_id}.jpg")
            if os.path.exists(thumbnail_path) and self.thumbnail_label.isVisible():
                try:
                    pixmap = QPixmap(thumbnail_path)
                    pixmap = pixmap.scaled(
                        self.thumbnail_label.width(), 
                        self.thumbnail_label.height(),
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(pixmap)
                except Exception:
                    pass  # 리사이즈 중 오류는 무시
        
        # 기간 레이블 위치 재조정
        if hasattr(self, 'duration_label') and hasattr(self, 'media_container'):
            self.duration_label.move(self.media_container.width() - 35, 5)
        
    def zoom_in(self):
        self.is_zoomed = True
        logger.info(f"{self.order+1}번 비디오 확대")
        
    def zoom_out(self):
        self.is_zoomed = False
        logger.info(f"{self.order+1}번 비디오 축소")


class WorkoutPage(QWidget):
    page_completed = pyqtSignal(int)  # 페이지 번호 전달
    
    def __init__(self, engine, page_id, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.page_id = page_id
        self.current_zoom_index = 0
        self.video_players = []
        self.start_countdown = 30  # 시작 카운트다운 (30초)
        self.is_page_completed = False  # 페이지 종료 여부 플래그
        
        self.load_config()
        self.load_videos()
        self.init_ui()
        self.setup_timers()
    
    def load_config(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        configs = {}
        for config in session.query(Config).all():
            configs[config.key] = config.value
        
        self.initial_delay = int(configs.get("initial_delay", 3))
        self.zoom_duration = int(configs.get("zoom_duration", 60))
        self.transition_duration = int(configs.get("transition_duration", 1))
        self.volume = int(configs.get("volume", 50))
        
        session.close()
    
    def load_videos(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        self.videos = []
        
        # 페이지에 할당된 영상을 순서대로 가져옴
        logger.info(f"페이지 {self.page_id}의 영상을 로딩합니다.")
        page_videos = session.query(PageVideo).filter_by(page_id=self.page_id).order_by(PageVideo.order).all()
        
        if not page_videos:
            logger.warning(f"페이지 {self.page_id}에 할당된 영상이 없습니다.")
        
        for pv in page_videos:
            video = session.query(Video).filter_by(id=pv.video_id).first()
            if video:
                logger.info(f"영상 {pv.order}: {video.title} ({video.url}), 길이: {video.duration}분")
                self.videos.append({
                    'order': pv.order,
                    'title': video.title,
                    'url': video.url,
                    'exercise_type': video.exercise_type,
                    'difficulty': video.difficulty,
                    'duration': video.duration  # 영상 길이 정보 추가 (분 단위)
                })
            else:
                logger.warning(f"영상 ID {pv.video_id}를 찾을 수 없습니다.")
        
        logger.info(f"총 {len(self.videos)}개 영상이 로드되었습니다.")
        session.close()
    
    def init_ui(self):
        # 세로 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2) # 간격을 줄여 이미지처럼 붙어보이게
        
        # 배경색 설정 - 검은색 배경
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#000000"))
        self.setPalette(palette)
        
        # 헤더 섹션 (로고 + 타이머)
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #151515; border-bottom: 1px solid #333;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        
        # 왼쪽 - 브랜드 로고
        logo_layout = QHBoxLayout()
        logo_label = QLabel("DREAMBODY")
        logo_label.setFont(QFont("Arial", 24, QFont.Bold))
        logo_label.setStyleSheet("color: white;")
        logo_layout.addWidget(logo_label)
        header_layout.addLayout(logo_layout)
        
        # 오른쪽 - 타이머
        timer_layout = QVBoxLayout()
        
        timer_label1 = QLabel("STARTS IN")
        timer_label1.setFont(QFont("Arial", 14))
        timer_label1.setAlignment(Qt.AlignRight)
        timer_label1.setStyleSheet("color: white;")
        
        self.timer_display = QLabel("00:30")
        self.timer_display.setFont(QFont("Arial", 32, QFont.Bold))
        self.timer_display.setAlignment(Qt.AlignRight)
        self.timer_display.setStyleSheet("color: white;")
        
        timer_layout.addWidget(timer_label1)
        timer_layout.addWidget(self.timer_display)
        header_layout.addLayout(timer_layout)
        
        main_layout.addWidget(header_frame)
        
        # 영상 컨테이너 (검은 배경에 흰색 영상)
        videos_container = QFrame()
        videos_container.setStyleSheet("background-color: #000000;")
        videos_layout = QVBoxLayout(videos_container)
        videos_layout.setContentsMargins(0, 0, 0, 0)
        videos_layout.setSpacing(2)
        
        # 영상 플레이어 추가
        logger.info(f"영상 플레이어 {len(self.videos)}개 추가")
        for video in self.videos:
            # 비디오 컨테이너 (번호 + 썸네일)
            video_container = QFrame()
            video_container.setStyleSheet("background-color: #000000;")
            video_layout = QHBoxLayout(video_container)
            video_layout.setContentsMargins(0, 0, 0, 0)
            
            # 번호 표시 (왼쪽)
            number_frame = QFrame()
            number_frame.setFixedWidth(60)
            number_frame.setStyleSheet("background-color: #000000;")
            number_layout = QVBoxLayout(number_frame)
            number_layout.setSpacing(2)
            number_layout.setContentsMargins(0, 5, 0, 5)
            
            # 번호 레이블
            number_label = QLabel(f"{video['order'] + 1:02d}")
            number_label.setFont(QFont("Arial", 30, QFont.Bold))
            number_label.setAlignment(Qt.AlignCenter)
            number_label.setStyleSheet("color: white;")
            number_layout.addWidget(number_label)
            
            # 타이머 레이블 추가
            # 영상 길이를 초 단위로 변환 (데이터베이스에는 분 단위로 저장)
            duration_seconds = int(video['duration'] * 60) if 'duration' in video and video['duration'] else self.zoom_duration
            timer_label = QLabel(f"{duration_seconds}s")
            timer_label.setFont(QFont("Arial", 16, QFont.Bold))
            timer_label.setAlignment(Qt.AlignCenter)
            timer_label.setStyleSheet("color: #AAAAAA;")
            number_layout.addWidget(timer_label)
            
            video_layout.addWidget(number_frame)
            
            # 비디오 플레이어
            player = VideoPlayer(video['order'], video['url'], video['title'], self)
            player.set_volume(self.volume)
            # 타이머 레이블 객체 저장
            player.timer_label = timer_label
            player.remaining_time = self.zoom_duration
            
            self.video_players.append(player)
            video_layout.addWidget(player, 1)
            
            videos_layout.addWidget(video_container)
        
        main_layout.addWidget(videos_container, 1)
        
        # 대기 메시지
        if not self.videos:
            no_video_label = QLabel("페이지에 할당된 영상이 없습니다.\n관리자 페이지에서 영상을 추가해주세요.")
            no_video_label.setFont(QFont("Arial", 18, QFont.Bold))
            no_video_label.setAlignment(Qt.AlignCenter)
            no_video_label.setStyleSheet("color: white; padding: 50px;")
            main_layout.addWidget(no_video_label)
            logger.warning("영상이 없어 대기 메시지 표시")
        
        self.update()
    
    def setup_timers(self):
        # 초기 타이머 설정 로깅
        logger.info(f"타이머 설정: 초기 딜레이 {self.initial_delay}초, 줌 지속시간 {self.zoom_duration}초")
        
        # 카운트다운 타이머
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 1초마다 업데이트
        logger.info("카운트다운 타이머 시작")
        
        # 초기 딜레이 타이머는 카운트다운 종료 후 시작됨
        self.initial_timer = QTimer(self)
        self.initial_timer.timeout.connect(self.zoom_first_video)
        self.initial_timer.setSingleShot(True)
        
        # 줌 전환 타이머
        self.zoom_timer = QTimer(self)
        self.zoom_timer.timeout.connect(self.switch_zoomed_video)
        
        # 영상 타이머 (1초마다 남은 시간 표시 업데이트)
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_video_timer)
        
        # 전체 프로세스 타이머 (마지막 영상 종료 후)
        self.completion_timer = QTimer(self)
        self.completion_timer.timeout.connect(self.complete_page)
        self.completion_timer.setSingleShot(True)
    
    def update_countdown(self):
        self.start_countdown -= 1
        minutes = self.start_countdown // 60
        seconds = self.start_countdown % 60
        self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")
        logger.info(f"카운트다운: {minutes:02d}:{seconds:02d}")
        
        if self.start_countdown <= 0:
            # 카운트다운 종료
            logger.info("카운트다운 종료")
            self.countdown_timer.stop()
            self.timer_display.setText("START")
            
            # 첫 영상 확대 타이머 시작
            logger.info("첫 영상 확대 타이머 시작")
            self.initial_timer.start(100)  # 거의 즉시 시작 (0.1초 후)
    
    def update_video_timer(self):
        # 이미 종료된 페이지인 경우 타이머 중지
        if self.is_page_completed:
            self.video_timer.stop()
            return
            
        # 현재 확대된 비디오의 남은 시간 업데이트
        if 0 <= self.current_zoom_index < len(self.video_players):
            player = self.video_players[self.current_zoom_index]
            player.remaining_time -= 1
            
            # 남은 시간 표시 업데이트
            player.timer_label.setText(f"{player.remaining_time}s")
            player.timer_label.setStyleSheet("color: #00FF76; font-weight: bold;")
            
            # 마지막 영상이고 타이머가 0 이하로 떨어졌을 때 즉시 종료
            if (self.current_zoom_index == len(self.video_players) - 1 and player.remaining_time <= 0):
                logger.info("마지막 영상 시간 종료, 페이지 종료")
                self.video_timer.stop()  # 타이머 중지
                self.complete_page()  # 페이지 완료 처리
                return  # 더 이상 진행하지 않음
            
            # 모든 비디오 플레이어의 타이머 레이블 스타일 설정
            for i, other_player in enumerate(self.video_players):
                if i != self.current_zoom_index:
                    # 비활성화된 타이머는 회색으로 표시
                    other_player.timer_label.setStyleSheet("color: #AAAAAA;")
                    
                    if i > self.current_zoom_index:
                        # 대기 중인 비디오는 기본 시간 표시
                        if i < len(self.videos) and 'duration' in self.videos[i] and self.videos[i]['duration']:
                            duration_seconds = int(self.videos[i]['duration'] * 60)
                            other_player.timer_label.setText(f"{duration_seconds}s")
                        else:
                            other_player.timer_label.setText(f"{self.zoom_duration}s")
                    else:
                        # 이미 재생된 비디오는 "완료" 표시
                        other_player.timer_label.setText("DONE")
            
            logger.info(f"비디오 {self.current_zoom_index + 1} 남은 시간: {player.remaining_time}초")
    
    def zoom_first_video(self):
        if self.video_players:
            logger.info("첫 번째 영상 확대 시작")
            
            # 모든 플레이어의 타이머 초기화
            for i, player in enumerate(self.video_players):
                # 각 영상의 실제 길이(초)로 타이머 설정
                if i < len(self.videos) and 'duration' in self.videos[i] and self.videos[i]['duration']:
                    duration_seconds = int(self.videos[i]['duration'] * 60)
                    player.remaining_time = duration_seconds
                    player.timer_label.setText(f"{duration_seconds}s")
                else:
                    player.remaining_time = self.zoom_duration
                    player.timer_label.setText(f"{self.zoom_duration}s")
                
            # 첫 번째 영상 확대 및 타이머 시작
            self.zoom_video(0)
            self.video_timer.start(1000)  # 1초마다 타이머 업데이트
            
            # 첫 번째 영상의 길이에 맞춰 다음 전환 타이머 설정
            if 'duration' in self.videos[0] and self.videos[0]['duration']:
                first_video_duration = int(self.videos[0]['duration'] * 60) * 1000  # 밀리초 단위로 변환
                logger.info(f"다음 영상 전환 타이머 시작 ({first_video_duration/1000}초)")
                self.zoom_timer.start(first_video_duration)
            else:
                logger.info(f"다음 영상 전환 타이머 시작 ({self.zoom_duration}초)")
                self.zoom_timer.start(self.zoom_duration * 1000)
        else:
            logger.warning("영상 플레이어가 없어 확대 불가")
    
    def switch_zoomed_video(self):
        # 다음 영상으로 전환
        next_index = self.current_zoom_index + 1
        
        # 현재 비디오의 타이머 표시를 "완료"로 변경
        if 0 <= self.current_zoom_index < len(self.video_players):
            current_player = self.video_players[self.current_zoom_index]
            current_player.timer_label.setText("DONE")
            current_player.timer_label.setStyleSheet("color: #AAAAAA;")
        
        if next_index < len(self.video_players):
            logger.info(f"다음 영상({next_index + 1}) 확대 시작")
            
            # 다음 비디오 타이머 초기화 - 실제 영상 길이 사용
            next_player = self.video_players[next_index]
            
            # 영상 길이 설정 (데이터베이스의 값 또는 기본값)
            if next_index < len(self.videos) and 'duration' in self.videos[next_index] and self.videos[next_index]['duration']:
                duration_seconds = int(self.videos[next_index]['duration'] * 60)
                next_player.remaining_time = duration_seconds
                next_player.timer_label.setText(f"{duration_seconds}s")
            else:
                next_player.remaining_time = self.zoom_duration
                next_player.timer_label.setText(f"{self.zoom_duration}s")
                
            next_player.timer_label.setStyleSheet("color: #00FF76; font-weight: bold;")
            
            # 비디오 확대 실행
            self.zoom_video(next_index)
            
            # 마지막 영상인 경우 종료 타이머 설정
            if next_index == len(self.video_players) - 1:
                # 마지막 영상의 실제 길이 사용
                if next_index < len(self.videos) and 'duration' in self.videos[next_index] and self.videos[next_index]['duration']:
                    last_video_duration = int(self.videos[next_index]['duration'] * 60) * 1000
                    logger.info(f"마지막 영상 확대 중, 종료 타이머 설정 ({last_video_duration/1000}초)")
                    self.zoom_timer.stop()
                    # 타이머는 설정하지만 백업으로 남겨두고 update_video_timer에서도 체크
                    self.completion_timer.start(last_video_duration + 1000)  # 1초 더 여유를 둠
                else:
                    logger.info(f"마지막 영상 확대 중, 종료 타이머 설정 ({self.zoom_duration}초)")
                    self.zoom_timer.stop()
                    self.completion_timer.start(self.zoom_duration * 1000 + 1000)  # 1초 더 여유를 둠
            else:
                # 다음 전환 타이머 설정 - 다음 영상의 실제 길이 사용
                if next_index < len(self.videos) and 'duration' in self.videos[next_index] and self.videos[next_index]['duration']:
                    next_video_duration = int(self.videos[next_index]['duration'] * 60) * 1000
                    logger.info(f"다음 영상 전환 타이머 시작 ({next_video_duration/1000}초)")
                    self.zoom_timer.start(next_video_duration)
                else:
                    logger.info(f"다음 영상 전환 타이머 시작 ({self.zoom_duration}초)")
                    self.zoom_timer.start(self.zoom_duration * 1000)
        else:
            # 모든 타이머 정지
            self.video_timer.stop()
            logger.info("모든 영상 재생 완료, 페이지 종료")
            self.complete_page()
    
    def zoom_video(self, index):
        if index < 0 or index >= len(self.video_players):
            logger.warning(f"잘못된 비디오 인덱스: {index}, 총 비디오 수: {len(self.video_players)}")
            return
            
        logger.info(f"비디오 {index + 1} 확대 시작")
        
        # 현재 줌 인덱스 업데이트
        self.current_zoom_index = index
        
        # 화면 높이 계산 - 세 영상이 동일한 크기로 표시
        for i, player in enumerate(self.video_players):
            # 모든 플레이어에 동일한 설정 적용
            player.setMinimumHeight(220)
            player.setMaximumHeight(220)
            
            if i == index:
                # 확대된 영상은 특별한 처리 없이 기본 크기 유지
                player.zoom_in()
                
                # 자동 재생 처리
                if not player.is_playing:
                    player.toggle_play()
            else:
                # 다른 비디오는 축소 상태만 설정
                player.zoom_out()
                
                # 재생 중이라면 정지
                if player.is_playing:
                    player.toggle_play()
                
        # UI 업데이트
        self.update()
        logger.info(f"비디오 {index + 1} 확대 완료")
    
    def complete_page(self):
        # 이미 종료 처리된 페이지인 경우 중복 실행 방지
        if self.is_page_completed:
            return
            
        # 종료 플래그 설정
        self.is_page_completed = True
        
        # 모든 타이머 정지
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if hasattr(self, 'initial_timer'):
            self.initial_timer.stop()
        if hasattr(self, 'zoom_timer'):
            self.zoom_timer.stop()
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()
        if hasattr(self, 'completion_timer'):
            self.completion_timer.stop()
            
        # 모든 영상 플레이어 정지
        for player in self.video_players:
            if player.is_playing:
                player.toggle_play()
        
        logger.info("페이지 완료 처리: 모든 타이머와 영상 정지")
        
        # 페이지 완료 시그널 발생
        self.page_completed.emit(self.page_id)
        
        # 창 닫기 (테스트 모드일 경우)
        if __name__ == "__main__":
            self.close()
    
    def resizeEvent(self, event):
        # 윈도우 크기가 변경될 때 영상 크기 즉시 조정 (애니메이션 없이)
        if hasattr(self, 'current_zoom_index') and len(self.video_players) > 0:
            total_height = self.height() - 100  # 헤더 영역 고려
            zoomed_height = int(total_height * 0.6)
            normal_height = int(total_height * 0.2)
            
            for i, player in enumerate(self.video_players):
                if i == self.current_zoom_index:
                    player.setFixedHeight(zoomed_height)
                else:
                    player.setFixedHeight(normal_height)
                    
        super().resizeEvent(event)


if __name__ == "__main__":
    from models import init_db
    
    app = QApplication(sys.argv)
    
    # 테스트용 DB 초기화
    engine = init_db()
    
    # 테스트 페이지 생성
    page = WorkoutPage(engine, 1)
    page.setWindowTitle("운동 영상 재생 테스트")
    page.resize(1080, 1920)  # 세로 화면
    page.show()
    
    sys.exit(app.exec_()) 