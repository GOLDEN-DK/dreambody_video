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
        logging.FileHandler('update_display_numbers.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.Update")

def main():
    """
    기존 PageVideo 테이블의 display_number를 order 값으로 업데이트
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
        
        # 현재 데이터 조회
        cursor.execute("SELECT id, page_id, video_id, \"order\", display_number FROM page_videos")
        rows = cursor.fetchall()
        
        logger.info(f"총 {len(rows)}개의 레코드를 찾았습니다.")
        
        # NULL인 display_number 업데이트
        updated = 0
        for row in rows:
            id, page_id, video_id, order, display_number = row
            
            if display_number is None:
                # display_number가 없는 경우 order + 1 값으로 설정
                new_display_number = order + 1
                cursor.execute(
                    "UPDATE page_videos SET display_number = ? WHERE id = ?", 
                    (new_display_number, id)
                )
                updated += 1
                logger.info(f"업데이트: ID={id}, page_id={page_id}, order={order}, display_number={new_display_number}")
        
        # 변경 사항 커밋
        conn.commit()
        logger.info(f"총 {updated}개 레코드 업데이트 완료!")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite 에러: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 