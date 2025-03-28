#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.Migration")

def main():
    """
    PageVideo 테이블에 display_number 필드를 추가하는 마이그레이션 스크립트
    """
    db_file = 'dreambody.db'
    
    if not os.path.exists(db_file):
        logger.error(f"데이터베이스 파일이 존재하지 않습니다: {db_file}")
        return
    
    # 데이터베이스 연결
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # display_number 컬럼 존재 여부 확인
        cursor.execute("PRAGMA table_info(page_videos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'display_number' in column_names:
            logger.info("이미 display_number 컬럼이 존재합니다.")
            return
        
        # 컬럼 추가
        logger.info("display_number 컬럼 추가 중...")
        cursor.execute("ALTER TABLE page_videos ADD COLUMN display_number INTEGER")
        
        # 기존 데이터 업데이트 - 기본적으로 order 값을 display_number에 설정
        logger.info("기존 데이터 업데이트 중...")
        cursor.execute('UPDATE page_videos SET display_number = "order"')
        
        # 변경 사항 커밋
        conn.commit()
        logger.info("마이그레이션 완료!")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite 에러: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 