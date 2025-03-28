import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dreambody.db')

# 데이터베이스 모델 정의
Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    url = Column(String(200), nullable=False)
    exercise_type = Column(String(50))  # 근력, 유산소 등
    difficulty = Column(String(20))  # 쉬움, 중간, 어려움 등
    duration = Column(Float)  # 영상 길이 (분 단위)
    
    page_videos = relationship("PageVideo", back_populates="video")
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title}', type='{self.exercise_type}')>"

class Page(Base):
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)  # "Page 1", "Page 2", "Page 3"
    # background_color 필드는 데이터베이스에 없으므로 주석 처리합니다
    # background_color = Column(String(20), default="#F5F5F5")
    
    page_videos = relationship("PageVideo", back_populates="page")
    
    def __repr__(self):
        return f"<Page(id={self.id}, name='{self.name}')>"

class PageVideo(Base):
    __tablename__ = 'page_videos'
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('pages.id'), nullable=False)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    order = Column(Integer, nullable=False)  # 1, 2, 3 (페이지 내 표시 순서)
    display_number = Column(Integer)  # 화면에 표시될 번호 (미설정 시 order+1 사용)
    
    page = relationship("Page", back_populates="page_videos")
    video = relationship("Video", back_populates="page_videos")
    
    def __repr__(self):
        return f"<PageVideo(page_id={self.page_id}, video_id={self.video_id}, order={self.order})>"

class Config(Base):
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    
    def __repr__(self):
        return f"<Config(key='{self.key}', value='{self.value}')>"

def init_db():
    # SQLite 데이터베이스 엔진 생성
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    # 모든 테이블 생성
    Base.metadata.create_all(engine)
    
    # 기본 설정값 추가
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Config 테이블에 기본값 설정
    default_configs = [
        {"key": "initial_delay", "value": "3"},
        {"key": "zoom_duration", "value": "60"},
        {"key": "transition_duration", "value": "1"},
        {"key": "volume", "value": "50"}
    ]
    
    # 기존 값 확인 후 없는 경우에만 추가
    for config in default_configs:
        existing = session.query(Config).filter_by(key=config["key"]).first()
        if not existing:
            session.add(Config(key=config["key"], value=config["value"]))
            
    session.commit()
    session.close()
    
    return engine

if __name__ == "__main__":
    print("데이터베이스 초기화 중...")
    engine = init_db()
    print(f"데이터베이스가 생성되었습니다: {DB_PATH}") 