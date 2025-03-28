#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from page import WorkoutPage
from models import init_db

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_page.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.TestPage")

def main():
    # 명령줄 인수 처리
    page_id = 1  # 기본값
    if len(sys.argv) > 1:
        try:
            page_id = int(sys.argv[1])
            logger.info(f"명령줄에서 페이지 ID {page_id}로 설정됨")
        except ValueError:
            logger.error(f"올바르지 않은 페이지 ID 형식: {sys.argv[1]}")
    
    app = QApplication(sys.argv)
    
    # 데이터베이스 엔진 초기화
    engine = init_db()
    
    # 테스트 페이지 생성
    logger.info(f"페이지 {page_id} 테스트 모드로 시작")
    page = WorkoutPage(engine, page_id, parent=None)
    page.start_countdown = 3  # 카운트다운 직접 설정
    
    # 독립 실행을 위한 설정
    page.setWindowTitle(f"드림바디 비디오 - 페이지 {page_id} 테스트")
    page.setMinimumSize(400, 700)  # 세로형 화면
    page.show()
    
    logger.info("테스트 페이지 애플리케이션 시작")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 