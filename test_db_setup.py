#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_setup.log')
    ]
)

logger = logging.getLogger("DreamBodyVideo.DBSetup")

# 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dreambody.db')

# 데이터베이스 모델 정의
Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    exercise_type = Column(String)
    difficulty = Column(String)
    duration = Column(Float)
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title}', type='{self.exercise_type}')>"

class Page(Base):
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<Page(id={self.id}, name='{self.name}')>"

class PageVideo(Base):
    __tablename__ = 'page_videos'
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('pages.id'))
    video_id = Column(Integer, ForeignKey('videos.id'))
    order = Column(Integer)
    
    def __repr__(self):
        return f"<PageVideo(page_id={self.page_id}, video_id={self.video_id}, order={self.order})>"

def init_db():
    # SQLite 데이터베이스 엔진 생성
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    # 모든 테이블 생성
    Base.metadata.create_all(engine)
    
    # 세션 생성
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return engine, session

def setup_test_data(session):
    # 현재 데이터 확인
    videos = session.query(Video).all()
    pages = session.query(Page).all()
    page_videos = session.query(PageVideo).all()
    
    logger.info(f"현재 DB 상태: {len(videos)}개 비디오, {len(pages)}개 페이지, {len(page_videos)}개 영상 할당")
    
    # 이미 데이터가 있으면 건너뛰기
    if videos and pages and page_videos:
        logger.info("데이터베이스에 이미 테스트 데이터가 존재합니다.")
        return
    
    # 페이지 생성 (1~3)
    if not pages:
        logger.info("페이지 데이터 생성 중...")
        for i in range(1, 4):
            page = Page(id=i, name=f"운동 페이지 {i}")
            session.add(page)
        session.commit()
        logger.info("3개 페이지 생성 완료")
    
    # 테스트 영상 데이터
    test_videos = [
        {
            "title": "5분 전신 스트레칭",
            "url": "https://www.youtube.com/watch?v=Tz9d7By2ytQ",
            "exercise_type": "스트레칭",
            "difficulty": "쉬움",
            "duration": 5.0
        },
        {
            "title": "10분 HIIT 운동",
            "url": "https://www.youtube.com/watch?v=f9N5xA3LPBg",
            "exercise_type": "HIIT",
            "difficulty": "중간",
            "duration": 10.0
        },
        {
            "title": "15분 복부 운동",
            "url": "https://www.youtube.com/watch?v=AnYl6Nk9GOA",
            "exercise_type": "복부",
            "difficulty": "중간",
            "duration": 15.0
        },
        {
            "title": "7분 허벅지 운동",
            "url": "https://www.youtube.com/watch?v=UBMk30rjy0o",
            "exercise_type": "하체",
            "difficulty": "중간",
            "duration": 7.0
        },
        {
            "title": "8분 팔 운동",
            "url": "https://www.youtube.com/watch?v=AnYl6Nk9GOA",
            "exercise_type": "상체",
            "difficulty": "어려움",
            "duration": 8.0
        },
        {
            "title": "5분 어깨 운동",
            "url": "https://www.youtube.com/watch?v=f9N5xA3LPBg",
            "exercise_type": "상체",
            "difficulty": "중간",
            "duration": 5.0
        },
        {
            "title": "12분 전신 운동",
            "url": "https://www.youtube.com/watch?v=Tz9d7By2ytQ",
            "exercise_type": "전신",
            "difficulty": "어려움",
            "duration": 12.0
        },
        {
            "title": "10분 코어 운동",
            "url": "https://www.youtube.com/watch?v=UBMk30rjy0o",
            "exercise_type": "코어",
            "difficulty": "중간",
            "duration": 10.0
        },
        {
            "title": "6분 마무리 스트레칭",
            "url": "https://www.youtube.com/watch?v=AnYl6Nk9GOA",
            "exercise_type": "스트레칭",
            "difficulty": "쉬움",
            "duration": 6.0
        }
    ]
    
    # 비디오 추가
    if not videos:
        logger.info("비디오 데이터 추가 중...")
        for video_data in test_videos:
            video = Video(**video_data)
            session.add(video)
        session.commit()
        logger.info(f"{len(test_videos)}개 테스트 비디오 추가 완료")
    
    # 페이지에 영상 할당
    if not page_videos:
        logger.info("페이지에 비디오 할당 중...")
        # 모든 영상 로드
        all_videos = session.query(Video).all()
        
        # 페이지당 3개씩 영상 할당
        for page_id in range(1, 4):
            # 각 페이지에 3개씩 할당 (순환)
            start_idx = (page_id - 1) * 3
            for i in range(3):
                video_idx = (start_idx + i) % len(all_videos)
                page_video = PageVideo(
                    page_id=page_id,
                    video_id=all_videos[video_idx].id,
                    order=i
                )
                session.add(page_video)
        
        session.commit()
        logger.info("페이지당 3개씩 비디오 할당 완료")

def main():
    logger.info("테스트 데이터베이스 설정 시작")
    
    # 데이터베이스 초기화
    engine, session = init_db()
    
    # 테스트 데이터 설정
    setup_test_data(session)
    
    # 설정 상태 확인
    videos = session.query(Video).all()
    pages = session.query(Page).all()
    page_videos = session.query(PageVideo).all()
    
    logger.info(f"테스트 데이터베이스 설정 완료: {len(videos)}개 비디오, {len(pages)}개 페이지, {len(page_videos)}개 영상 할당")
    
    # 페이지 1번에 할당된 비디오 확인
    page1_videos = session.query(PageVideo).filter_by(page_id=1).all()
    logger.info(f"페이지 1 할당된 비디오: {len(page1_videos)}개")
    
    for pv in page1_videos:
        video = session.query(Video).filter_by(id=pv.video_id).first()
        logger.info(f"  - 순서 {pv.order}: {video.title} ({video.url})")
    
    # 세션 종료
    session.close()
    
    logger.info("테스트 데이터베이스 설정이 완료되었습니다.")
    logger.info(f"현재 데이터베이스 경로: {DB_PATH}")

if __name__ == "__main__":
    main() 