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
        logging.FileHandler('fix_display_numbers.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.Fix")

def main():
    """
    페이지 1의 표시 번호를 1, 2, 3으로 수정하는 스크립트
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
        
        # 페이지 1의 영상 정보 조회
        cursor.execute('SELECT id, "order" FROM page_videos WHERE page_id = 1 ORDER BY "order"')
        rows = cursor.fetchall()
        
        logger.info(f"페이지 1의 총 {len(rows)}개 영상 정보를 찾았습니다.")
        
        # 표시 번호 업데이트
        for i, row in enumerate(rows):
            id, order = row
            display_number = i + 1  # 1, 2, 3으로 설정
            
            cursor.execute(
                "UPDATE page_videos SET display_number = ? WHERE id = ?", 
                (display_number, id)
            )
            logger.info(f"업데이트: ID={id}, 순서={order}, 새 표시번호={display_number}")
        
        # 변경 사항 커밋
        conn.commit()
        logger.info("페이지 1의 표시 번호 수정 완료!")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite 에러: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 