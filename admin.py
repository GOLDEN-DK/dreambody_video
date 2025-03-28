import sys
import re
from PyQt5.QtCore import Qt, QUrl, QRegExp
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QTableWidget, 
                           QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QLineEdit, QFormLayout, QComboBox, QSpinBox, QMessageBox, 
                           QHeaderView, QDialog, QDialogButtonBox, QGroupBox)
from PyQt5.QtGui import QPixmap, QRegExpValidator
from PyQt5.QtWebEngineWidgets import QWebEngineView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, Page, PageVideo, Config


class AddEditVideoDialog(QDialog):
    def __init__(self, video=None, parent=None):
        super().__init__(parent)
        self.video = video
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("영상 추가/수정")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        # 영상 URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("YouTube URL (https://youtube.com/watch?v=...)")
        form_layout.addRow("URL:", self.url_edit)
        
        # 영상 제목
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("영상 제목")
        form_layout.addRow("제목:", self.title_edit)
        
        # 운동 타입
        self.type_combo = QComboBox()
        self.type_combo.addItems(["근력", "유산소", "스트레칭", "유연성", "균형", "기타"])
        form_layout.addRow("운동 타입:", self.type_combo)
        
        # 난이도
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["쉬움", "중간", "어려움"])
        form_layout.addRow("난이도:", self.difficulty_combo)
        
        # 영상 길이 레이아웃 (분:초)
        duration_layout = QHBoxLayout()
        
        # 분 입력
        self.duration_min_spin = QSpinBox()
        self.duration_min_spin.setRange(0, 60)
        self.duration_min_spin.setValue(5)
        self.duration_min_spin.setSuffix(" 분")
        duration_layout.addWidget(self.duration_min_spin)
        
        # 구분자
        separator_label = QLabel(":")
        separator_label.setAlignment(Qt.AlignCenter)
        separator_label.setStyleSheet("font-weight: bold;")
        duration_layout.addWidget(separator_label)
        
        # 초 입력
        self.duration_sec_spin = QSpinBox()
        self.duration_sec_spin.setRange(0, 59)
        self.duration_sec_spin.setValue(0)
        self.duration_sec_spin.setSuffix(" 초")
        duration_layout.addWidget(self.duration_sec_spin)
        
        # 여백 추가
        duration_layout.addStretch()
        
        form_layout.addRow("길이:", duration_layout)
        
        layout.addLayout(form_layout)
        
        # 미리보기 그룹
        preview_group = QGroupBox("영상 미리보기")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_btn = QPushButton("미리보기 불러오기")
        self.preview_btn.clicked.connect(self.load_preview)
        preview_layout.addWidget(self.preview_btn)
        
        self.web_view = QWebEngineView()
        self.web_view.setFixedHeight(200)
        preview_layout.addWidget(self.web_view)
        
        layout.addWidget(preview_group)
        
        # 다이얼로그 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # 기존 데이터 로드
        if self.video:
            self.url_edit.setText(self.video.url)
            self.title_edit.setText(self.video.title)
            
            # 콤보박스 인덱스 설정
            if self.video.exercise_type:
                type_index = self.type_combo.findText(self.video.exercise_type)
                if type_index >= 0:
                    self.type_combo.setCurrentIndex(type_index)
            
            if self.video.difficulty:
                diff_index = self.difficulty_combo.findText(self.video.difficulty)
                if diff_index >= 0:
                    self.difficulty_combo.setCurrentIndex(diff_index)
            
            if self.video.duration:
                # 분과 초 분리
                minutes = int(self.video.duration)
                seconds = int((self.video.duration - minutes) * 60)
                
                self.duration_min_spin.setValue(minutes)
                self.duration_sec_spin.setValue(seconds)
    
    def load_preview(self):
        url = self.url_edit.text()
        if not url:
            return
        
        # YouTube URL을 임베드 URL로 변환
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}"
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1]
            embed_url = f"https://www.youtube.com/embed/{video_id}"
        else:
            embed_url = url
        
        self.web_view.setUrl(QUrl(embed_url))
    
    def get_video_data(self):
        # 분과 초를 합쳐서 duration 계산 (분 단위로 저장)
        minutes = self.duration_min_spin.value()
        seconds = self.duration_sec_spin.value()
        duration = minutes + (seconds / 60.0)
        
        return {
            'url': self.url_edit.text(),
            'title': self.title_edit.text(),
            'exercise_type': self.type_combo.currentText(),
            'difficulty': self.difficulty_combo.currentText(),
            'duration': duration
        }


class AdminWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.session_maker = sessionmaker(bind=engine)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("운동 영상 관리 시스템")
        self.setMinimumSize(1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 타이틀
        title_label = QLabel("운동 영상 관리 시스템")
        title_label.setFont(self.font())
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #333; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        
        # 영상 목록 탭
        self.videos_tab = QWidget()
        self.init_videos_tab()
        self.tabs.addTab(self.videos_tab, "영상 목록")
        
        # 페이지별 설정 탭
        self.page_settings_tab = QWidget()
        self.init_page_settings_tab()
        self.tabs.addTab(self.page_settings_tab, "페이지별 설정")
        
        # 시스템 설정 탭
        self.system_settings_tab = QWidget()
        self.init_system_settings_tab()
        self.tabs.addTab(self.system_settings_tab, "시스템 설정")
        
        main_layout.addWidget(self.tabs)
        
        # 페이지 실행 버튼
        run_layout = QHBoxLayout()
        run_layout.addStretch()
        
        self.run_page1_btn = QPushButton("1번 페이지 실행")
        self.run_page1_btn.clicked.connect(lambda: self.run_page(1))
        run_layout.addWidget(self.run_page1_btn)
        
        self.run_page2_btn = QPushButton("2번 페이지 실행")
        self.run_page2_btn.clicked.connect(lambda: self.run_page(2))
        run_layout.addWidget(self.run_page2_btn)
        
        self.run_page3_btn = QPushButton("3번 페이지 실행")
        self.run_page3_btn.clicked.connect(lambda: self.run_page(3))
        run_layout.addWidget(self.run_page3_btn)
        
        run_layout.addStretch()
        main_layout.addLayout(run_layout)
    
    def init_videos_tab(self):
        layout = QVBoxLayout(self.videos_tab)
        
        # 테이블 위젯
        self.videos_table = QTableWidget()
        self.videos_table.setColumnCount(6)
        self.videos_table.setHorizontalHeaderLabels(["ID", "제목", "URL", "운동 타입", "난이도", "길이(분:초)"])
        self.videos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.videos_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.videos_table)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        self.add_video_btn = QPushButton("영상 추가")
        self.add_video_btn.clicked.connect(self.add_video)
        button_layout.addWidget(self.add_video_btn)
        
        self.edit_video_btn = QPushButton("영상 수정")
        self.edit_video_btn.clicked.connect(self.edit_video)
        button_layout.addWidget(self.edit_video_btn)
        
        self.delete_video_btn = QPushButton("영상 삭제")
        self.delete_video_btn.clicked.connect(self.delete_video)
        button_layout.addWidget(self.delete_video_btn)
        
        self.refresh_video_btn = QPushButton("새로고침")
        self.refresh_video_btn.clicked.connect(self.load_videos)
        button_layout.addWidget(self.refresh_video_btn)
        
        layout.addLayout(button_layout)
        
        # 초기 데이터 로드
        self.load_videos()
    
    def init_page_settings_tab(self):
        layout = QVBoxLayout(self.page_settings_tab)
        
        # 페이지 선택 영역
        page_select_layout = QHBoxLayout()
        
        page_select_layout.addWidget(QLabel("페이지 선택:"))
        
        self.page_combo = QComboBox()
        self.load_pages()
        self.page_combo.currentIndexChanged.connect(self.load_page_videos)
        page_select_layout.addWidget(self.page_combo)
        
        page_select_layout.addStretch()
        
        layout.addLayout(page_select_layout)
        
        # 페이지에 할당된 영상 영역
        assignments_group = QGroupBox("페이지에 할당된 영상 (3개)")
        assignments_layout = QVBoxLayout(assignments_group)
        
        # 1번 영상 할당
        self.video1_layout = QHBoxLayout()
        self.video1_layout.addWidget(QLabel("1번 영상:"))
        self.video1_combo = QComboBox()
        self.video1_layout.addWidget(self.video1_combo, 1)
        
        # 1번 영상 표시 번호
        self.video1_layout.addWidget(QLabel("표시 번호:"))
        self.display_num1_spin = QSpinBox()
        self.display_num1_spin.setRange(1, 99)
        self.display_num1_spin.setValue(1)
        self.video1_layout.addWidget(self.display_num1_spin)
        
        assignments_layout.addLayout(self.video1_layout)
        
        # 2번 영상 할당
        self.video2_layout = QHBoxLayout()
        self.video2_layout.addWidget(QLabel("2번 영상:"))
        self.video2_combo = QComboBox()
        self.video2_layout.addWidget(self.video2_combo, 1)
        
        # 2번 영상 표시 번호
        self.video2_layout.addWidget(QLabel("표시 번호:"))
        self.display_num2_spin = QSpinBox()
        self.display_num2_spin.setRange(1, 99)
        self.display_num2_spin.setValue(2)
        self.video2_layout.addWidget(self.display_num2_spin)
        
        assignments_layout.addLayout(self.video2_layout)
        
        # 3번 영상 할당
        self.video3_layout = QHBoxLayout()
        self.video3_layout.addWidget(QLabel("3번 영상:"))
        self.video3_combo = QComboBox()
        self.video3_layout.addWidget(self.video3_combo, 1)
        
        # 3번 영상 표시 번호
        self.video3_layout.addWidget(QLabel("표시 번호:"))
        self.display_num3_spin = QSpinBox()
        self.display_num3_spin.setRange(1, 99)
        self.display_num3_spin.setValue(3)
        self.video3_layout.addWidget(self.display_num3_spin)
        
        assignments_layout.addLayout(self.video3_layout)
        
        layout.addWidget(assignments_group)
        
        # 설명 추가
        help_label = QLabel("※ 표시 번호는 영상 앞에 표시될 번호입니다. 실제 재생 순서는 왼쪽의 '1번, 2번, 3번' 지정에 의해 결정됩니다.")
        help_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(help_label)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_page_btn = QPushButton("페이지 설정 저장")
        self.save_page_btn.clicked.connect(self.save_page_settings)
        save_layout.addWidget(self.save_page_btn)
        
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        # 영상 콤보박스 초기화
        self.load_video_combos()
        
        # 초기 페이지 영상 로드
        if self.page_combo.count() > 0:
            self.load_page_videos()
    
    def init_system_settings_tab(self):
        layout = QVBoxLayout(self.system_settings_tab)
        
        settings_group = QGroupBox("시스템 설정")
        settings_form = QFormLayout(settings_group)
        
        # 설정 필드
        self.initial_delay_spin = QSpinBox()
        self.initial_delay_spin.setRange(1, 10)
        self.initial_delay_spin.setSuffix(" 초")
        settings_form.addRow("시작 후 확대까지 대기 시간:", self.initial_delay_spin)
        
        self.zoom_duration_spin = QSpinBox()
        self.zoom_duration_spin.setRange(10, 300)
        self.zoom_duration_spin.setSuffix(" 초")
        settings_form.addRow("확대 상태 지속 시간:", self.zoom_duration_spin)
        
        self.transition_duration_spin = QSpinBox()
        self.transition_duration_spin.setRange(1, 5)
        self.transition_duration_spin.setSuffix(" 초")
        settings_form.addRow("확대/축소 애니메이션 지속 시간:", self.transition_duration_spin)
        
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setSuffix(" %")
        settings_form.addRow("기본 볼륨:", self.volume_spin)
        
        layout.addWidget(settings_group)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_settings_btn = QPushButton("시스템 설정 저장")
        self.save_settings_btn.clicked.connect(self.save_system_settings)
        save_layout.addWidget(self.save_settings_btn)
        
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        # 초기 설정값 로드
        self.load_system_settings()
    
    def load_videos(self):
        # 세션 생성
        session = self.session_maker()
        
        # 모든 비디오 가져오기
        videos = session.query(Video).all()
        
        # 테이블 설정
        self.videos_table.setRowCount(len(videos))
        
        # 데이터 표시
        for i, video in enumerate(videos):
            self.videos_table.setItem(i, 0, QTableWidgetItem(str(video.id)))
            self.videos_table.setItem(i, 1, QTableWidgetItem(video.title))
            self.videos_table.setItem(i, 2, QTableWidgetItem(video.url))
            self.videos_table.setItem(i, 3, QTableWidgetItem(video.exercise_type or ""))
            self.videos_table.setItem(i, 4, QTableWidgetItem(video.difficulty or ""))
            
            # 길이를 분:초 형식으로 표시
            if video.duration is not None:
                minutes = int(video.duration)
                seconds = int((video.duration - minutes) * 60)
                duration_text = f"{minutes}:{seconds:02d}"
            else:
                duration_text = ""
            self.videos_table.setItem(i, 5, QTableWidgetItem(duration_text))
        
        # 테이블 크기 조정
        self.videos_table.resizeColumnsToContents()
        
        # 세션 종료
        session.close()
    
    def add_video(self):
        dialog = AddEditVideoDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            video_data = dialog.get_video_data()
            
            session = self.session_maker()
            new_video = Video(
                title=video_data['title'],
                url=video_data['url'],
                exercise_type=video_data['exercise_type'],
                difficulty=video_data['difficulty'],
                duration=video_data['duration']
            )
            
            session.add(new_video)
            session.commit()
            session.close()
            
            # 테이블 새로고침
            self.load_videos()
            self.load_video_combos()
    
    def edit_video(self):
        selected_items = self.videos_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "수정할 영상을 선택해주세요.")
            return
        
        # 선택된 행의 ID 열 텍스트 가져오기
        row = selected_items[0].row()
        video_id = int(self.videos_table.item(row, 0).text())
        
        session = self.session_maker()
        video = session.query(Video).filter_by(id=video_id).first()
        
        if not video:
            QMessageBox.warning(self, "오류", "선택한 영상을 찾을 수 없습니다.")
            session.close()
            return
        
        dialog = AddEditVideoDialog(video, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            video_data = dialog.get_video_data()
            
            video.title = video_data['title']
            video.url = video_data['url']
            video.exercise_type = video_data['exercise_type']
            video.difficulty = video_data['difficulty']
            video.duration = video_data['duration']
            
            session.commit()
        
        session.close()
        
        # 테이블 새로고침
        self.load_videos()
        self.load_video_combos()
    
    def delete_video(self):
        selected_items = self.videos_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "삭제할 영상을 선택해주세요.")
            return
        
        # 선택된 행의 ID 열 텍스트 가져오기
        row = selected_items[0].row()
        video_id = int(self.videos_table.item(row, 0).text())
        title = self.videos_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "영상 삭제 확인", 
            f"'{title}' 영상을 정말 삭제하시겠습니까?\n\n"
            "이 영상이 페이지에 할당되어 있다면, 해당 할당도 함께 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            session = self.session_maker()
            
            # 먼저 페이지 할당 삭제
            session.query(PageVideo).filter_by(video_id=video_id).delete()
            
            # 영상 삭제
            session.query(Video).filter_by(id=video_id).delete()
            
            session.commit()
            session.close()
            
            # 테이블 새로고침
            self.load_videos()
            self.load_video_combos()
            self.load_page_videos()
    
    def load_pages(self):
        self.page_combo.clear()
        
        session = self.session_maker()
        pages = session.query(Page).all()
        
        for page in pages:
            self.page_combo.addItem(page.name, page.id)
        
        session.close()
    
    def load_video_combos(self):
        # 모든 비디오 콤보박스 초기화
        for combo in [self.video1_combo, self.video2_combo, self.video3_combo]:
            combo.clear()
            combo.addItem("-- 선택 안 함 --", None)
        
        session = self.session_maker()
        videos = session.query(Video).all()
        
        for video in videos:
            for combo in [self.video1_combo, self.video2_combo, self.video3_combo]:
                combo.addItem(f"{video.id}: {video.title}", video.id)
        
        session.close()
    
    def load_page_videos(self):
        if self.page_combo.count() == 0:
            return
            
        page_id = self.page_combo.currentData()
        
        session = self.session_maker()
        
        # 현재 할당된 영상 정보 찾기
        video_infos = {1: {'id': None, 'display_number': 1}, 
                       2: {'id': None, 'display_number': 2}, 
                       3: {'id': None, 'display_number': 3}}
        
        page_videos = session.query(PageVideo).filter_by(page_id=page_id).all()
        
        for pv in page_videos:
            video_infos[pv.order]['id'] = pv.video_id
            video_infos[pv.order]['display_number'] = pv.display_number if pv.display_number is not None else pv.order
        
        # 콤보박스 선택 업데이트
        for order, combo, spin in [
            (1, self.video1_combo, self.display_num1_spin), 
            (2, self.video2_combo, self.display_num2_spin), 
            (3, self.video3_combo, self.display_num3_spin)
        ]:
            video_id = video_infos[order]['id']
            display_number = video_infos[order]['display_number']
            
            # 스핀 박스 값 설정
            spin.setValue(display_number)
            
            index = 0  # 기본값: 선택 안 함
            if video_id:
                # 아이디가 일치하는 인덱스 찾기
                for i in range(combo.count()):
                    if combo.itemData(i) == video_id:
                        index = i
                        break
            
            combo.setCurrentIndex(index)
        
        session.close()
    
    def save_page_settings(self):
        if self.page_combo.count() == 0:
            return
            
        page_id = self.page_combo.currentData()
        
        video1_id = self.video1_combo.currentData()
        video2_id = self.video2_combo.currentData()
        video3_id = self.video3_combo.currentData()
        
        display_num1 = self.display_num1_spin.value()
        display_num2 = self.display_num2_spin.value()
        display_num3 = self.display_num3_spin.value()
        
        # 필수 영상 확인
        missing_videos = []
        if not video1_id:
            missing_videos.append("1번")
        if not video2_id:
            missing_videos.append("2번")
        if not video3_id:
            missing_videos.append("3번")
        
        if missing_videos:
            QMessageBox.warning(
                self, "경고", 
                f"각 페이지에는 3개의 영상이 모두 필요합니다. 영상을 선택해주세요: {', '.join(missing_videos)}"
            )
            return
        
        session = self.session_maker()
        
        # 기존 할당 삭제
        session.query(PageVideo).filter_by(page_id=page_id).delete()
        
        # 새로운 할당 추가
        new_assignments = [
            PageVideo(page_id=page_id, video_id=video1_id, order=1, display_number=display_num1),
            PageVideo(page_id=page_id, video_id=video2_id, order=2, display_number=display_num2),
            PageVideo(page_id=page_id, video_id=video3_id, order=3, display_number=display_num3)
        ]
        
        session.add_all(new_assignments)
        session.commit()
        session.close()
        
        QMessageBox.information(
            self, "성공", 
            f"페이지 '{self.page_combo.currentText()}'에 영상이 성공적으로 할당되었습니다."
        )
    
    def load_system_settings(self):
        session = self.session_maker()
        
        # 모든 설정값 가져오기
        configs = {}
        for config in session.query(Config).all():
            configs[config.key] = config.value
        
        # 스핀박스 값 설정
        self.initial_delay_spin.setValue(int(configs.get("initial_delay", 3)))
        self.zoom_duration_spin.setValue(int(configs.get("zoom_duration", 60)))
        self.transition_duration_spin.setValue(int(configs.get("transition_duration", 1)))
        self.volume_spin.setValue(int(configs.get("volume", 50)))
        
        session.close()
    
    def save_system_settings(self):
        session = self.session_maker()
        
        # 설정 업데이트
        settings = {
            "initial_delay": str(self.initial_delay_spin.value()),
            "zoom_duration": str(self.zoom_duration_spin.value()),
            "transition_duration": str(self.transition_duration_spin.value()),
            "volume": str(self.volume_spin.value())
        }
        
        for key, value in settings.items():
            config = session.query(Config).filter_by(key=key).first()
            if config:
                config.value = value
        
        session.commit()
        session.close()
        
        QMessageBox.information(self, "성공", "시스템 설정이 저장되었습니다.")
    
    def run_page(self, page_id):
        # 해당 페이지에 영상이 할당되어 있는지 확인
        session = self.session_maker()
        page_videos = session.query(PageVideo).filter_by(page_id=page_id).all()
        session.close()
        
        if len(page_videos) < 3:
            QMessageBox.warning(
                self, "경고", 
                f"{page_id}번 페이지에는 3개의 영상이 모두 필요합니다. 페이지를 먼저 설정해주세요."
            )
            return
        
        # 페이지 실행
        from page import WorkoutPage
        
        # 메인 윈도우는 그대로 유지하면서 페이지를 별도 창으로 실행
        self.workout_page = WorkoutPage(self.engine, page_id)
        self.workout_page.setWindowTitle(f"운동 페이지 {page_id}")
        self.workout_page.resize(1080, 1920)  # 세로 화면
        self.workout_page.show()
        
        # 페이지 종료 시그널 연결
        self.workout_page.page_completed.connect(self.on_page_completed)
    
    def on_page_completed(self, page_id):
        self.workout_page.close()
        QMessageBox.information(
            self, "페이지 완료", 
            f"{page_id}번 페이지의 영상 재생이 완료되었습니다."
        )


if __name__ == "__main__":
    from models import init_db
    
    app = QApplication(sys.argv)
    
    # DB 초기화
    engine = init_db()
    
    # 관리자 창 생성
    admin = AdminWindow(engine)
    admin.show()
    
    sys.exit(app.exec_()) 