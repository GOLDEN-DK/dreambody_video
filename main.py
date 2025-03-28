#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from admin import AdminWindow
from models import init_db

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DreamBodyVideo")

def main():
    """
    운동 영상 재생 시스템 시작 함수
    """
    logger.info("애플리케이션 시작")
    
    # PyQT 디버깅 활성화
    os.environ["QT_DEBUG_PLUGINS"] = "1"
    
    # OpenGL 관련 오류 방지를 위한 환경 변수 설정
    os.environ["QT_OPENGL"] = "software"  # 소프트웨어 렌더링 사용
    logger.info("소프트웨어 렌더링 모드 사용")
    
    # 어플리케이션 설정
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # 소프트웨어 OpenGL 사용
    
    # WebEngine 보안 설정
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # YouTube API를 사용하기 위한 명령행 인수 추가
    sys.argv.append("--disable-web-security")
    sys.argv.append("--no-sandbox")
    sys.argv.append("--allow-file-access-from-files")
    
    logger.info("QApplication 생성")
    # 기본 YouTube 접근을 위한 CORS 설정
    app = QApplication(sys.argv)
    
    # 글로벌 웹 설정
    logger.info("WebEngine 설정 구성")
    settings = QWebEngineSettings.globalSettings()
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
    settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
    settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
    
    # 데이터베이스 초기화
    logger.info("데이터베이스 초기화")
    engine = init_db()
    
    # 관리자 창 시작
    logger.info("관리자 창 생성")
    admin = AdminWindow(engine)
    admin.show()
    
    # 앱 실행
    logger.info("애플리케이션 실행")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 