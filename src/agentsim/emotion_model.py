"""
情绪量化模型 - 基于心理学理论的多维度情绪表示
支持情绪状态的数值化表示和归一化处理

理论基础：
1. 基本情绪理论 (Ekman) - 6种基本情绪：快乐、悲伤、恐惧、愤怒、惊讶、厌恶
2. 情绪维度理论 (Russell) - 效价和唤醒度二维模型
3. PAD情绪模型 (Mehrabian & Russell) - 三维情绪空间：愉悦度、唤醒度、支配感
4. Plutchik情绪轮盘 - 8种基本情绪及其混合形式
5. 认知评估理论 (Lazarus) - 情绪源于情境认知评估
6. 社会学情绪理论 (Hochschild) - 情绪的社会建构和情绪劳动
"""

import random
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class EmotionDimension(Enum):
    """情绪维度枚举 - 扩展的多维情绪模型"""
    # PAD三维模型 (Pleasure-Arousal-Dominance)
    VALENCE = "valence"        # 效价 (愉悦度): -1.0 (极不愉快) 到 1.0 (极愉快)
    AROUSAL = "arousal"        # 唤醒度: -1.0 (极度平静) 到 1.0 (高度兴奋)
    DOMINANCE = "dominance"    # 支配感: -1.0 (完全顺从) 到 1.0 (完全支配)

    # 基本情绪维度 (Ekman + 扩展)
    JOY = "joy"               # 快乐: -0.5 (极度沮丧) 到 1.0 (极度快乐)
    SADNESS = "sadness"       # 悲伤: -0.5 (轻微不悦) 到 1.0 (极度悲伤)
    ANGER = "anger"           # 愤怒: -0.5 (轻微烦躁) 到 1.0 (极度愤怒)
    FEAR = "fear"             # 恐惧: -0.5 (轻微担忧) 到 1.0 (极度恐惧)
    SURPRISE = "surprise"     # 惊讶: -1.0 (极度震惊) 到 1.0 (极度惊讶)
    DISGUST = "disgust"       # 厌恶: -0.5 (轻微反感) 到 1.0 (极度厌恶)

    # 社会情绪维度
    TRUST = "trust"           # 信任: -1.0 (完全不信任) 到 1.0 (完全信任)
    ANTICIPATION = "anticipation"  # 期待: -0.5 (焦虑) 到 1.0 (兴奋期待)

    # 复合情绪维度 (基于Plutchik轮盘理论)
    OPTIMISM = "optimism"     # 乐观: -0.5 (悲观) 到 1.0 (极度乐观)
    ANXIETY = "anxiety"       # 焦虑: -0.5 (平静) 到 1.0 (极度焦虑)
    GUILT = "guilt"           # 内疚: -0.5 (自豪) 到 1.0 (极度内疚)
    PRIDE = "pride"           # 自豪: -0.5 (羞愧) 到 1.0 (极度自豪)
    SHAME = "shame"           # 羞耻: -0.5 (自信) 到 1.0 (极度羞耻)
    ENVY = "envy"             # 嫉妒: -0.5 (羡慕) 到 1.0 (极度嫉妒)
    GRATITUDE = "gratitude"   # 感激: -0.5 (怨恨) 到 1.0 (极度感激)
    HOPE = "hope"             # 希望: -0.5 (绝望) 到 1.0 (极度希望)


@dataclass
class EmotionProfile:
    """情绪画像类 - 包含多个情绪维度的数值，支持负值和更丰富的情绪表达"""

    # PAD三维模型维度
    valence: float = 0.0      # 效价: -1.0 到 1.0
    arousal: float = 0.0      # 唤醒度: -1.0 到 1.0 (支持负值表示过度平静)
    dominance: float = 0.0    # 支配感: -1.0 到 1.0 (支持负值表示过度顺从)

    # 基本情绪维度 - 支持负值表示相反情绪
    joy: float = 0.0          # 快乐: -0.5 到 1.0 (负值表示沮丧)
    sadness: float = 0.0      # 悲伤: -0.5 到 1.0 (负值表示愉悦)
    anger: float = 0.0        # 愤怒: -0.5 到 1.0 (负值表示平静)
    fear: float = 0.0         # 恐惧: -0.5 到 1.0 (负值表示勇敢)
    surprise: float = 0.0     # 惊讶: -1.0 到 1.0 (负值表示完全预期)
    disgust: float = 0.0      # 厌恶: -0.5 到 1.0 (负值表示欣赏)

    # 社会情绪维度
    trust: float = 0.0        # 信任: -1.0 到 1.0 (负值表示怀疑)
    anticipation: float = 0.0 # 期待: -0.5 到 1.0 (负值表示焦虑)

    # 复合情绪维度
    optimism: float = 0.0     # 乐观: -0.5 到 1.0 (负值表示悲观)
    anxiety: float = 0.0      # 焦虑: -0.5 到 1.0 (负值表示放松)
    guilt: float = 0.0        # 内疚: -0.5 到 1.0 (负值表示自豪)
    pride: float = 0.0        # 自豪: -0.5 到 1.0 (负值表示羞愧)
    shame: float = 0.0        # 羞耻: -0.5 到 1.0 (负值表示自信)
    envy: float = 0.0         # 嫉妒: -0.5 到 1.0 (负值表示满足)
    gratitude: float = 0.0    # 感激: -0.5 到 1.0 (负值表示怨恨)
    hope: float = 0.0         # 希望: -0.5 到 1.0 (负值表示绝望)

    # 情绪元数据
    timestamp: Optional[float] = None  # 情绪记录时间戳
    context: str = ""         # 情绪产生的上下文
    intensity: float = 0.0    # 情绪总体强度
    
    def __post_init__(self):
        """初始化后验证和归一化所有数值"""
        self.normalize()
        if self.timestamp is None:
            self.timestamp = np.datetime64('now').astype(float)
    
    def normalize(self) -> None:
        """归一化所有情绪数值到有效范围内"""
        # PAD维度
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))

        # 基本情绪维度 - 支持负值但限制范围（需要回写到属性上）
        for name in [
            "joy", "sadness", "anger", "fear",
            "disgust", "anticipation", "optimism",
            "anxiety", "guilt", "pride", "shame",
            "envy", "gratitude", "hope",
        ]:
            value = getattr(self, name)
            setattr(self, name, max(-0.5, min(1.0, value)))

        # 社会情绪维度
        self.trust = max(-1.0, min(1.0, self.trust))
        self.surprise = max(-1.0, min(1.0, self.surprise))

        # 计算情绪强度
        self._calculate_intensity()

    def _calculate_intensity(self) -> None:
        """计算情绪总体强度"""
        # 基于PAD维度的强度计算
        pad_intensity = np.sqrt(self.valence**2 + self.arousal**2 + self.dominance**2) / np.sqrt(3)

        # 基于基本情绪维度的强度计算
        basic_emotions = [self.joy, self.sadness, self.anger, self.fear,
                         self.surprise, self.disgust, self.trust, self.anticipation]
        basic_intensity = np.mean([abs(e) for e in basic_emotions])

        # 综合强度
        self.intensity = (pad_intensity + basic_intensity) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，包含所有情绪维度和元数据"""
        return {
            # PAD维度
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "dominance": round(self.dominance, 3),

            # 基本情绪维度
            "joy": round(self.joy, 3),
            "sadness": round(self.sadness, 3),
            "anger": round(self.anger, 3),
            "fear": round(self.fear, 3),
            "surprise": round(self.surprise, 3),
            "disgust": round(self.disgust, 3),

            # 社会情绪维度
            "trust": round(self.trust, 3),
            "anticipation": round(self.anticipation, 3),

            # 复合情绪维度
            "optimism": round(self.optimism, 3),
            "anxiety": round(self.anxiety, 3),
            "guilt": round(self.guilt, 3),
            "pride": round(self.pride, 3),
            "shame": round(self.shame, 3),
            "envy": round(self.envy, 3),
            "gratitude": round(self.gratitude, 3),
            "hope": round(self.hope, 3),

            # 元数据
            "intensity": round(self.intensity, 3),
            "timestamp": self.timestamp,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionProfile':
        """从字典创建情绪画像"""
        return cls(
            valence=float(data.get("valence", 0.0)),
            arousal=float(data.get("arousal", 0.0)),
            dominance=float(data.get("dominance", 0.0)),
            joy=float(data.get("joy", 0.0)),
            sadness=float(data.get("sadness", 0.0)),
            anger=float(data.get("anger", 0.0)),
            fear=float(data.get("fear", 0.0)),
            surprise=float(data.get("surprise", 0.0)),
            disgust=float(data.get("disgust", 0.0)),
            trust=float(data.get("trust", 0.0)),
            anticipation=float(data.get("anticipation", 0.0)),
            optimism=float(data.get("optimism", 0.0)),
            anxiety=float(data.get("anxiety", 0.0)),
            guilt=float(data.get("guilt", 0.0)),
            pride=float(data.get("pride", 0.0)),
            shame=float(data.get("shame", 0.0)),
            envy=float(data.get("envy", 0.0)),
            gratitude=float(data.get("gratitude", 0.0)),
            hope=float(data.get("hope", 0.0)),
            timestamp=data.get("timestamp"),
            context=data.get("context", "")
        )
    
    def get_primary_emotions(self) -> List[Tuple[str, float]]:
        """获取主要情绪列表（强度最高的几个情绪）"""
        # 所有情绪维度及其强度
        all_emotions = {
            "joy": self.joy,
            "sadness": self.sadness,
            "anger": self.anger,
            "fear": self.fear,
            "surprise": self.surprise,
            "disgust": self.disgust,
            "trust": self.trust,
            "anticipation": self.anticipation,
            "optimism": self.optimism,
            "anxiety": self.anxiety,
            "guilt": self.guilt,
            "pride": self.pride,
            "shame": self.shame,
            "envy": self.envy,
            "gratitude": self.gratitude,
            "hope": self.hope
        }

        # 过滤出强度大于阈值的情绪
        significant_emotions = [(name, value) for name, value in all_emotions.items()
                               if abs(value) > 0.2]

        # 按强度绝对值排序
        significant_emotions.sort(key=lambda x: abs(x[1]), reverse=True)

        # 返回强度最高的前3个情绪
        return significant_emotions[:3]

    def get_primary_emotion(self) -> str:
        """获取主要情绪标签（向后兼容）"""
        primary_emotions = self.get_primary_emotions()
        if primary_emotions:
            return primary_emotions[0][0]
        return "neutral"

    def get_mood_description(self) -> str:
        """获取情绪描述文本，支持多维情绪"""
        primary_emotions = self.get_primary_emotions()

        if not primary_emotions:
                return "neutral"
        
        # 如果有强烈的PAD情绪，使用PAD描述
        if abs(self.valence) > 0.4 or abs(self.arousal) > 0.4 or abs(self.dominance) > 0.4:
            valence_desc = "positive" if self.valence > 0.3 else "negative" if self.valence < -0.3 else "neutral"
            arousal_desc = "excited" if self.arousal > 0.3 else "calm" if self.arousal < -0.3 else "balanced"
            dominance_desc = "confident" if self.dominance > 0.3 else "submissive" if self.dominance < -0.3 else "moderate"

            return f"{valence_desc} and {arousal_desc} ({dominance_desc})"

        # 否则使用基本情绪描述
        emotion_names = [emotion[0] for emotion in primary_emotions]
        intensity = abs(primary_emotions[0][1])
        
        intensity_desc = ""
        if intensity > 0.8:
            intensity_desc = "extremely "
        elif intensity > 0.6:
            intensity_desc = "very "
        elif intensity > 0.4:
            intensity_desc = "moderately "
        elif intensity > 0.2:
            intensity_desc = "slightly "
        
        if len(emotion_names) == 1:
            return f"{intensity_desc}{emotion_names[0]}"
        elif len(emotion_names) == 2:
            return f"{intensity_desc}{emotion_names[0]} and {emotion_names[1]}"
        else:
            return f"{intensity_desc}{', '.join(emotion_names[:-1])} and {emotion_names[-1]}"

    def get_emotion_quadrant(self) -> str:
        """基于PAD模型获取情绪象限"""
        if self.valence > 0.2 and self.arousal > 0.2:
            return "excited"
        elif self.valence > 0.2 and self.arousal < -0.2:
            return "relaxed"
        elif self.valence < -0.2 and self.arousal > 0.2:
            return "anxious"
        elif self.valence < -0.2 and self.arousal < -0.2:
            return "depressed"
        else:
            return "neutral"

    def get_emotional_balance(self) -> Dict[str, float]:
        """获取情绪平衡分析"""
        positive_emotions = [self.joy, self.optimism, self.pride, self.gratitude, self.hope]
        negative_emotions = [self.sadness, self.anger, self.fear, self.disgust, self.shame, self.envy]

        positive_sum = sum(positive_emotions)
        negative_sum = sum(negative_emotions)

        total = positive_sum + negative_sum

        return {
            "positive_balance": positive_sum / total if total > 0 else 0,
            "negative_balance": negative_sum / total if total > 0 else 0,
            "emotional_stability": 1 - abs(positive_sum - negative_sum) / total if total > 0 else 0
        }

    def similarity(self, other: 'EmotionProfile') -> float:
        """计算与另一个情绪画像的相似度"""
        # 计算所有维度的欧几里得距离
        dimensions = [
            self.valence, self.arousal, self.dominance,
            self.joy, self.sadness, self.anger, self.fear, self.surprise, self.disgust,
            self.trust, self.anticipation, self.optimism, self.anxiety,
            self.guilt, self.pride, self.shame, self.envy, self.gratitude, self.hope
        ]

        other_dimensions = [
            other.valence, other.arousal, other.dominance,
            other.joy, other.sadness, other.anger, other.fear, other.surprise, other.disgust,
            other.trust, other.anticipation, other.optimism, other.anxiety,
            other.guilt, other.pride, other.shame, other.envy, other.gratitude, other.hope
        ]

        # 计算欧几里得距离
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(dimensions, other_dimensions)))

        # 转换为相似度 (0-1之间，1表示完全相同)
        max_distance = np.sqrt(len(dimensions) * 4)  # 最大可能距离 (2^2 * 维度数)
        similarity = 1 - (distance / max_distance)

        return max(0.0, min(1.0, similarity))

    def blend_with(self, other: 'EmotionProfile', weight: float = 0.5) -> 'EmotionProfile':
        """与另一个情绪画像混合"""
        return EmotionProfile(
            valence=self.valence * (1 - weight) + other.valence * weight,
            arousal=self.arousal * (1 - weight) + other.arousal * weight,
            dominance=self.dominance * (1 - weight) + other.dominance * weight,
            joy=self.joy * (1 - weight) + other.joy * weight,
            sadness=self.sadness * (1 - weight) + other.sadness * weight,
            anger=self.anger * (1 - weight) + other.anger * weight,
            fear=self.fear * (1 - weight) + other.fear * weight,
            surprise=self.surprise * (1 - weight) + other.surprise * weight,
            disgust=self.disgust * (1 - weight) + other.disgust * weight,
            trust=self.trust * (1 - weight) + other.trust * weight,
            anticipation=self.anticipation * (1 - weight) + other.anticipation * weight,
            optimism=self.optimism * (1 - weight) + other.optimism * weight,
            anxiety=self.anxiety * (1 - weight) + other.anxiety * weight,
            guilt=self.guilt * (1 - weight) + other.guilt * weight,
            pride=self.pride * (1 - weight) + other.pride * weight,
            shame=self.shame * (1 - weight) + other.shame * weight,
            envy=self.envy * (1 - weight) + other.envy * weight,
            gratitude=self.gratitude * (1 - weight) + other.gratitude * weight,
            hope=self.hope * (1 - weight) + other.hope * weight,
            context=f"blend of '{self.context}' and '{other.context}'"
        )


class EmotionGenerator:
    """情绪生成器 - 根据情境和人格生成合适的情绪状态，支持多维情绪"""
    
    # 基于心理学理论的复合情绪模板
    EMOTION_TEMPLATES = {
        # 基础情绪模板
        "neutral": EmotionProfile(
            valence=0.0, arousal=0.0, dominance=0.0,
            context="neutral emotional state"
        ),
        "calm": EmotionProfile(
            valence=0.3, arousal=-0.3, dominance=0.2, trust=0.4, anxiety=-0.4,
            context="calm and relaxed"
        ),
        "excited": EmotionProfile(
            valence=0.8, arousal=0.8, dominance=0.4, joy=0.8, anticipation=0.6, hope=0.5,
            context="excited and energetic"
        ),
        "anxious": EmotionProfile(
            valence=-0.4, arousal=0.7, dominance=-0.3, anxiety=0.8, fear=0.5, anticipation=-0.4,
            context="anxious and worried"
        ),
        "angry": EmotionProfile(
            valence=-0.7, arousal=0.8, dominance=0.6, anger=0.9, disgust=0.4,
            context="angry and frustrated"
        ),
        "sad": EmotionProfile(
            valence=-0.8, arousal=-0.4, dominance=-0.5, sadness=0.9, hope=-0.5, optimism=-0.6,
            context="sad and melancholic"
        ),
        "fearful": EmotionProfile(
            valence=-0.6, arousal=0.8, dominance=-0.7, fear=0.9, anxiety=0.7, surprise=-0.3,
            context="fearful and scared"
        ),
        "surprised": EmotionProfile(
            valence=0.3, arousal=0.9, dominance=0.0, surprise=0.9, anticipation=0.4,
            context="surprised and amazed"
        ),
        "disgusted": EmotionProfile(
            valence=-0.6, arousal=0.4, dominance=0.2, disgust=0.9, anger=0.5,
            context="disgusted and repelled"
        ),

        # 社会情绪模板
        "trusting": EmotionProfile(
            valence=0.5, arousal=-0.2, dominance=0.3, trust=0.8, gratitude=0.4,
            context="trusting and faithful"
        ),
        "suspicious": EmotionProfile(
            valence=-0.4, arousal=0.3, dominance=-0.2, trust=-0.7, anxiety=0.5, anticipation=-0.3,
            context="suspicious and distrustful"
        ),
        "confident": EmotionProfile(
            valence=0.7, arousal=0.4, dominance=0.8, pride=0.7, optimism=0.6,
            context="confident and assured"
        ),
        "shy": EmotionProfile(
            valence=-0.2, arousal=-0.4, dominance=-0.6, shame=0.4, anxiety=0.3,
            context="shy and timid"
        ),

        # 复合情绪模板（基于Plutchik理论）
        "hopeful": EmotionProfile(
            valence=0.6, arousal=0.3, dominance=0.4, hope=0.8, anticipation=0.5, optimism=0.7,
            context="hopeful and optimistic"
        ),
        "guilty": EmotionProfile(
            valence=-0.5, arousal=-0.3, dominance=-0.4, guilt=0.8, shame=0.6, sadness=0.4,
            context="guilty and remorseful"
        ),
        "proud": EmotionProfile(
            valence=0.7, arousal=0.5, dominance=0.7, pride=0.9, joy=0.6, gratitude=0.4,
            context="proud and accomplished"
        ),
        "envious": EmotionProfile(
            valence=-0.3, arousal=0.4, dominance=-0.2, envy=0.8, sadness=0.4, anger=0.3,
            context="envious and jealous"
        ),
        "grateful": EmotionProfile(
            valence=0.8, arousal=0.3, dominance=0.4, gratitude=0.9, joy=0.6, trust=0.5,
            context="grateful and appreciative"
        ),

        # 认知评估情绪模板
        "threatened": EmotionProfile(
            valence=-0.6, arousal=0.8, dominance=-0.5, fear=0.8, anger=0.5, anxiety=0.7,
            context="threatened and defensive"
        ),
        "challenged": EmotionProfile(
            valence=0.2, arousal=0.7, dominance=0.6, anticipation=0.6, hope=0.4, pride=0.3,
            context="challenged and motivated"
        ),
        "supported": EmotionProfile(
            valence=0.7, arousal=0.2, dominance=0.4, gratitude=0.7, trust=0.6, joy=0.5,
            context="supported and valued"
        ),
        "ignored": EmotionProfile(
            valence=-0.4, arousal=-0.3, dominance=-0.3, sadness=0.6, shame=0.4, envy=0.3,
            context="ignored and insignificant"
        ),
    }
    
    @classmethod
    def generate_from_template(cls, template_name: str, variation: float = 0.2, context: str = "") -> EmotionProfile:
        """从模板生成情绪，添加随机变化和上下文信息"""
        if template_name not in cls.EMOTION_TEMPLATES:
            template_name = "neutral"
        
        base = cls.EMOTION_TEMPLATES[template_name]
        
        # 添加随机变化
        new_emotion = EmotionProfile(
            valence=base.valence + random.uniform(-variation, variation),
            arousal=base.arousal + random.uniform(-variation, variation),
            dominance=base.dominance + random.uniform(-variation, variation),
            joy=base.joy + random.uniform(-variation, variation),
            sadness=base.sadness + random.uniform(-variation, variation),
            anger=base.anger + random.uniform(-variation, variation),
            fear=base.fear + random.uniform(-variation, variation),
            surprise=base.surprise + random.uniform(-variation, variation),
            disgust=base.disgust + random.uniform(-variation, variation),
            trust=base.trust + random.uniform(-variation, variation),
            anticipation=base.anticipation + random.uniform(-variation, variation),
            optimism=base.optimism + random.uniform(-variation, variation),
            anxiety=base.anxiety + random.uniform(-variation, variation),
            guilt=base.guilt + random.uniform(-variation, variation),
            pride=base.pride + random.uniform(-variation, variation),
            shame=base.shame + random.uniform(-variation, variation),
            envy=base.envy + random.uniform(-variation, variation),
            gratitude=base.gratitude + random.uniform(-variation, variation),
            hope=base.hope + random.uniform(-variation, variation),
            context=context or base.context
        )

        return new_emotion
    
    @classmethod
    def generate_from_context(cls, context: str, personality: Dict[str, Any]) -> EmotionProfile:
        """根据上下文和人格生成情绪，支持多维情绪分析"""

        # 人格基础影响
        base_personality = cls._analyze_personality_traits(personality)

        # 上下文情绪分析
        context_emotions = cls._analyze_context_emotions(context)

        # 合并人格和上下文影响
        combined_emotions = cls._combine_emotions(base_personality, context_emotions, context)

        return combined_emotions

    @classmethod
    def _analyze_personality_traits(cls, personality: Dict[str, Any]) -> EmotionProfile:
        """分析人格特质对情绪的影响"""
        base_emotion = EmotionProfile(context="personality baseline")

        description = personality.get("description", "").lower()

        # 乐观主义者
        if any(word in description for word in ["optimistic", "positive", "hopeful"]):
            base_emotion.valence += 0.3
            base_emotion.optimism += 0.4
            base_emotion.hope += 0.3

        # 悲观主义者
        if any(word in description for word in ["pessimistic", "negative", "cynical"]):
            base_emotion.valence -= 0.3
            base_emotion.optimism -= 0.4
            base_emotion.anxiety += 0.2

        # 自信者
        if any(word in description for word in ["confident", "assertive", "bold"]):
            base_emotion.dominance += 0.3
            base_emotion.pride += 0.2

        # 害羞者
        if any(word in description for word in ["shy", "timid", "introverted"]):
            base_emotion.dominance -= 0.3
            base_emotion.shame += 0.2
            base_emotion.arousal -= 0.2

        # 外向者
        if any(word in description for word in ["extroverted", "outgoing", "sociable"]):
            base_emotion.arousal += 0.2
            base_emotion.anticipation += 0.2

        # 内向者
        if any(word in description for word in ["introverted", "reserved", "quiet"]):
            base_emotion.arousal -= 0.2

        return base_emotion

    @classmethod
    def _analyze_context_emotions(cls, context: str) -> EmotionProfile:
        """分析上下文中的情绪关键词（支持中英文）"""
        emotion = EmotionProfile(context=f"context: {context}")

        context_lower = context.lower()

        # 积极情绪关键词
        positive_keywords = {
            "joy": ["happy", "joy", "delighted", "pleased", "satisfied"],
            "gratitude": ["thankful", "grateful", "appreciative"],
            "pride": ["proud", "accomplished", "successful"],
            "hope": ["hopeful", "optimistic", "looking forward"],
            "trust": ["trust", "reliable", "dependable"],
            "love": ["love", "affection", "care"]
        }

        # 消极情绪关键词
        negative_keywords = {
            "sadness": ["sad", "unhappy", "depressed", "melancholy", "sorrow"],
            "anger": ["angry", "mad", "frustrated", "irritated", "annoyed"],
            "fear": ["scared", "frightened", "terrified", "afraid", "worried"],
            "disgust": ["disgusted", "repelled", "revolted", "grossed out"],
            "shame": ["ashamed", "embarrassed", "humiliated"],
            "guilt": ["guilty", "remorseful", "regretful"],
            "envy": ["envious", "jealous", "covetous"],
            "anxiety": ["anxious", "nervous", "worried", "stressed"]
        }

        # 情境关键词（含中文）
        situation_keywords = {
            "threat": ["threat", "danger", "risk", "menace", "hazard", "威胁", "危险"],
            "challenge": ["challenge", "obstacle", "difficulty", "problem", "挑战", "困难"],
            "support": ["support", "help", "assistance", "aid", "支持", "帮助"],
            "rejection": ["rejected", "ignored", "excluded", "dismissed", "拒绝", "忽视"],
            "success": ["success", "achievement", "victory", "triumph", "成功", "胜利"],
            "failure": ["failure", "defeat", "loss", "disappointment", "失败", "挫败"],
            "surprise": ["surprise", "unexpected", "sudden", "shocking", "惊讶", "意外"]
        }

        # 分析情绪关键词
        for emotion_type, keywords in positive_keywords.items():
            if any(word in context_lower for word in keywords):
                intensity = sum(1 for word in keywords if word in context_lower) / len(keywords)
                setattr(emotion, emotion_type, min(0.8, emotion.joy + intensity * 0.8))

        for emotion_type, keywords in negative_keywords.items():
            if any(word in context_lower for word in keywords):
                intensity = sum(1 for word in keywords if word in context_lower) / len(keywords)
                current_value = getattr(emotion, emotion_type, 0)
                setattr(emotion, emotion_type, min(1.0, current_value + intensity * 0.8))

        # 分析情境影响
        for situation, keywords in situation_keywords.items():
            if any(word in context_lower for word in keywords):
                if situation == "threat":
                    emotion.fear += 0.6
                    emotion.anxiety += 0.4
                    emotion.valence -= 0.4
                    emotion.arousal += 0.5
                elif situation == "challenge":
                    emotion.anticipation += 0.5
                    emotion.hope += 0.3
                    emotion.arousal += 0.3
                elif situation == "support":
                    emotion.gratitude += 0.5
                    emotion.trust += 0.4
                    emotion.valence += 0.3
                elif situation == "rejection":
                    emotion.shame += 0.4
                    emotion.sadness += 0.3
                    emotion.valence -= 0.4
                elif situation == "success":
                    emotion.pride += 0.6
                    emotion.joy += 0.5
                    emotion.valence += 0.5
                elif situation == "failure":
                    emotion.sadness += 0.6
                    emotion.shame += 0.3
                    emotion.valence -= 0.5
                elif situation == "surprise":
                    emotion.surprise += 0.7
                    emotion.arousal += 0.4
        
        return emotion
    
    @classmethod
    def _combine_emotions(cls, personality: EmotionProfile, context: EmotionProfile, context_str: str) -> EmotionProfile:
        """合并人格基础情绪和上下文情绪"""
        # 权重平衡：人格占40%，上下文占60%
        personality_weight = 0.4
        context_weight = 0.6

        combined = EmotionProfile(
            valence=personality.valence * personality_weight + context.valence * context_weight,
            arousal=personality.arousal * personality_weight + context.arousal * context_weight,
            dominance=personality.dominance * personality_weight + context.dominance * context_weight,
            joy=personality.joy * personality_weight + context.joy * context_weight,
            sadness=personality.sadness * personality_weight + context.sadness * context_weight,
            anger=personality.anger * personality_weight + context.anger * context_weight,
            fear=personality.fear * personality_weight + context.fear * context_weight,
            surprise=personality.surprise * personality_weight + context.surprise * context_weight,
            disgust=personality.disgust * personality_weight + context.disgust * context_weight,
            trust=personality.trust * personality_weight + context.trust * context_weight,
            anticipation=personality.anticipation * personality_weight + context.anticipation * context_weight,
            optimism=personality.optimism * personality_weight + context.optimism * context_weight,
            anxiety=personality.anxiety * personality_weight + context.anxiety * context_weight,
            guilt=personality.guilt * personality_weight + context.guilt * context_weight,
            pride=personality.pride * personality_weight + context.pride * context_weight,
            shame=personality.shame * personality_weight + context.shame * context_weight,
            envy=personality.envy * personality_weight + context.envy * context_weight,
            gratitude=personality.gratitude * personality_weight + context.gratitude * context_weight,
            hope=personality.hope * personality_weight + context.hope * context_weight,
            context=f"personality + context: {context_str}"
        )

        return combined

    @classmethod
    def evolve_emotion(cls, current: EmotionProfile, context: str, personality: Dict[str, Any],
                      time_decay: float = 0.1) -> EmotionProfile:
        """基于当前情绪和上下文演化情绪状态，支持情绪衰减"""
        # 获取上下文影响
        context_emotion = cls.generate_from_context(context, personality)
        
        # 情绪稳定性参数（基于人格）
        stability = cls._calculate_emotional_stability(personality)

        # 时间衰减效应（情绪会随时间衰减）
        decay_factor = 1.0 - time_decay

        # 计算新情绪 (当前情绪 + 上下文影响，考虑稳定性)
        new_emotion = EmotionProfile(
            valence=current.valence * stability * decay_factor + context_emotion.valence * (1 - stability),
            arousal=current.arousal * stability * decay_factor + context_emotion.arousal * (1 - stability),
            dominance=current.dominance * stability * decay_factor + context_emotion.dominance * (1 - stability),
            joy=current.joy * stability * decay_factor + context_emotion.joy * (1 - stability),
            sadness=current.sadness * stability * decay_factor + context_emotion.sadness * (1 - stability),
            anger=current.anger * stability * decay_factor + context_emotion.anger * (1 - stability),
            fear=current.fear * stability * decay_factor + context_emotion.fear * (1 - stability),
            surprise=current.surprise * stability * decay_factor + context_emotion.surprise * (1 - stability),
            disgust=current.disgust * stability * decay_factor + context_emotion.disgust * (1 - stability),
            trust=current.trust * stability * decay_factor + context_emotion.trust * (1 - stability),
            anticipation=current.anticipation * stability * decay_factor + context_emotion.anticipation * (1 - stability),
            optimism=current.optimism * stability * decay_factor + context_emotion.optimism * (1 - stability),
            anxiety=current.anxiety * stability * decay_factor + context_emotion.anxiety * (1 - stability),
            guilt=current.guilt * stability * decay_factor + context_emotion.guilt * (1 - stability),
            pride=current.pride * stability * decay_factor + context_emotion.pride * (1 - stability),
            shame=current.shame * stability * decay_factor + context_emotion.shame * (1 - stability),
            envy=current.envy * stability * decay_factor + context_emotion.envy * (1 - stability),
            gratitude=current.gratitude * stability * decay_factor + context_emotion.gratitude * (1 - stability),
            hope=current.hope * stability * decay_factor + context_emotion.hope * (1 - stability),
            context=f"evolved: {context}"
        )
        
        return new_emotion

    @classmethod
    def _calculate_emotional_stability(cls, personality: Dict[str, Any]) -> float:
        """计算情绪稳定性（基于人格特质）"""
        description = personality.get("description", "").lower()

        base_stability = 0.7  # 默认中等稳定性

        # 情绪稳定特质
        if any(word in description for word in ["stable", "calm", "steady", "reliable"]):
            base_stability += 0.2

        # 情绪不稳定特质
        if any(word in description for word in ["volatile", "moody", "unstable", "emotional"]):
            base_stability -= 0.2

        # 内向者通常更情绪稳定
        if any(word in description for word in ["introverted", "reserved", "thoughtful"]):
            base_stability += 0.1

        # 外向者通常更情绪活跃但不一定不稳定
        if any(word in description for word in ["extroverted", "outgoing", "energetic"]):
            base_stability -= 0.05  # 轻微降低稳定性以反映更高的反应性

        return max(0.3, min(0.9, base_stability))  # 限制在合理范围内


def parse_legacy_mood(mood_str: str) -> EmotionProfile:
    """解析传统的mood字符串为情绪画像，支持新情绪模型"""
    mood_lower = mood_str.lower().strip()
    
    # 扩展的情绪映射（包含新情绪）
    mood_mapping = {
        # 原有映射
        "calm": "calm",
        "neutral": "neutral", 
        "curious": "excited",
        "anxious": "anxious",
        "worried": "anxious",
        "nervous": "anxious",
        "angry": "angry",
        "mad": "angry",
        "frustrated": "angry",
        "sad": "sad",
        "depressed": "sad",
        "melancholy": "sad",
        "happy": "excited",
        "joyful": "excited",
        "cheerful": "excited",
        "excited": "excited",
        "fearful": "fearful",
        "scared": "fearful",
        "terrified": "fearful",
        "surprised": "surprised",
        "shocked": "surprised",
        "confident": "confident",
        "suspicious": "suspicious",

        # 新增情绪映射
        "hopeful": "hopeful",
        "hopeless": "sad",
        "proud": "proud",
        "ashamed": "guilty",
        "guilty": "guilty",
        "envious": "envious",
        "jealous": "envious",
        "grateful": "grateful",
        "thankful": "grateful",
        "trusting": "trusting",
        "distrustful": "suspicious",
        "shy": "shy",
        "threatened": "threatened",
        "challenged": "challenged",
        "supported": "supported",
        "ignored": "ignored",
        "disgusted": "disgusted",
        "repelled": "disgusted",
        "optimistic": "hopeful",
        "pessimistic": "sad",
        "embarrassed": "guilty",
        "humiliated": "guilty",
        "confused": "surprised",
        "amazed": "surprised",
        "shocked": "surprised",
        "ecstatic": "excited",
        "devastated": "sad",
        "furious": "angry",
        "terrified": "fearful",
        "panicked": "fearful",
        "content": "calm",
        "satisfied": "calm",
        "relaxed": "calm",
        "peaceful": "calm",
        "agitated": "anxious",
        "restless": "anxious",
        "tense": "anxious",
        "stressed": "anxious",
        "overwhelmed": "anxious",
        "bitter": "angry",
        "resentful": "angry",
        "indignant": "angry",
        "heartbroken": "sad",
        "miserable": "sad",
        "despairing": "sad",
        "petrified": "fearful",
        "horrified": "fearful",
        "apprehensive": "anxious",
        "uneasy": "anxious",
        "insecure": "anxious",
        "vulnerable": "fearful",
        "exposed": "fearful",
        "intimidated": "fearful",
        "bullied": "threatened",
        "victimized": "threatened",
        "betrayed": "threatened",
        "loved": "excited",
        "cherished": "grateful",
        "valued": "proud",
        "respected": "proud",
        "admired": "proud",
        "included": "supported",
        "welcomed": "supported",
        "accepted": "supported",
        "rejected": "ignored",
        "excluded": "ignored",
        "isolated": "ignored",
        "abandoned": "ignored",
        "lonely": "sad",
        "nostalgic": "sad",
        "sentimental": "grateful",
        "accomplished": "proud",
        "successful": "proud",
        "victorious": "proud",
        "defeated": "sad",
        "humiliated": "guilty",
        "embarrassed": "guilty",
        "regretful": "guilty",
        "remorseful": "guilty",
        "covetous": "envious",
        "resentful": "envious",
        "dissatisfied": "envious",
        "appreciative": "grateful",
        "indebted": "grateful",
        "obliged": "grateful",
        "faithful": "trusting",
        "loyal": "trusting",
        "devoted": "trusting",
        "skeptical": "suspicious",
        "doubtful": "suspicious",
        "wary": "suspicious",
        "timid": "shy",
        "bashful": "shy",
        "reserved": "shy",
        "motivated": "challenged",
        "inspired": "hopeful",
        "encouraged": "supported",
        "discouraged": "sad",
        "disheartened": "sad",
        "demotivated": "ignored"
    }
    
    template_name = mood_mapping.get(mood_lower, "neutral")
    return EmotionGenerator.generate_from_template(template_name, context=f"legacy mood: {mood_str}")


def create_emotion_summary(emotion: EmotionProfile) -> str:
    """创建情绪摘要文本，支持多维情绪展示"""
    description = emotion.get_mood_description()
    
    # 创建详细的情绪摘要
    summary_parts = [description]

    # 添加PAD维度信息
    pad_info = []
    if abs(emotion.valence) > 0.2:
        pad_info.append(f"valence: {emotion.valence:+.2f}")
    if abs(emotion.arousal) > 0.2:
        pad_info.append(f"arousal: {emotion.arousal:+.2f}")
    if abs(emotion.dominance) > 0.2:
        pad_info.append(f"dominance: {emotion.dominance:+.2f}")

    if pad_info:
        summary_parts.append(f"({', '.join(pad_info)})")

    # 添加主要情绪维度（强度大于0.3的）
    significant_emotions = []
    for dim_name, value in emotion.to_dict().items():
        if dim_name in ["joy", "sadness", "anger", "fear", "surprise", "disgust",
                       "trust", "anticipation", "optimism", "anxiety", "guilt",
                       "pride", "shame", "envy", "gratitude", "hope"]:
            if abs(value) > 0.3:
                significant_emotions.append(f"{dim_name}: {value:+.2f}")

    if significant_emotions:
        summary_parts.append(f"[{' '.join(significant_emotions)}]")

    # 添加情绪强度和上下文信息
    if emotion.intensity > 0.1:
        summary_parts.append(f"intensity: {emotion.intensity:.2f}")

    if emotion.context:
        summary_parts.append(f"context: {emotion.context}")

    return " | ".join(summary_parts)

def analyze_emotion_dynamics(emotions: List[EmotionProfile]) -> Dict[str, Any]:
    """分析情绪动态变化"""
    if len(emotions) < 2:
        return {"error": "需要至少两个情绪样本"}

    analysis = {
        "total_samples": len(emotions),
        "time_span": emotions[-1].timestamp - emotions[0].timestamp if emotions[0].timestamp else 0,
        "emotion_trends": {},
        "stability_metrics": {},
        "dominant_emotions": {},
        "mood_shifts": []
    }

    # 计算情绪趋势
    all_dimensions = set()
    for emotion in emotions:
        all_dimensions.update(emotion.to_dict().keys())

    for dim in all_dimensions:
        if dim in ["timestamp", "context", "intensity"]:
            continue

        values = [getattr(e, dim, 0) for e in emotions]
        analysis["emotion_trends"][dim] = {
            "start": values[0],
            "end": values[-1],
            "change": values[-1] - values[0],
            "volatility": np.std(values) if len(values) > 1 else 0
        }

    # 计算稳定性指标
    pad_values = [[e.valence, e.arousal, e.dominance] for e in emotions]
    pad_stability = 1 - np.mean([np.std([v[i] for v in pad_values]) for i in range(3)])

    analysis["stability_metrics"] = {
        "pad_stability": pad_stability,
        "overall_intensity_trend": analysis["emotion_trends"]["intensity"]["change"] if "intensity" in analysis["emotion_trends"] else 0
    }

    # 识别主要情绪
    dominant_counts = {}
    for emotion in emotions:
        primary = emotion.get_primary_emotion()
        dominant_counts[primary] = dominant_counts.get(primary, 0) + 1

    analysis["dominant_emotions"] = dict(sorted(dominant_counts.items(), key=lambda x: x[1], reverse=True)[:3])

    # 检测情绪转变点
    for i in range(1, len(emotions)):
        prev_emotion = emotions[i-1]
        curr_emotion = emotions[i]

        # 计算情绪变化幅度
        change_magnitude = abs(curr_emotion.valence - prev_emotion.valence) + abs(curr_emotion.arousal - prev_emotion.arousal)

        if change_magnitude > 0.5:  # 显著变化阈值
            analysis["mood_shifts"].append({
                "from_tick": i-1,
                "to_tick": i,
                "change_magnitude": change_magnitude,
                "from_emotion": prev_emotion.get_primary_emotion(),
                "to_emotion": curr_emotion.get_primary_emotion()
            })

    return analysis


class EmotionAnalytics:
    """情绪分析和可视化工具"""

    @staticmethod
    def create_emotion_heatmap_data(emotions: List[EmotionProfile]) -> Dict[str, Any]:
        """创建情绪热力图数据"""
        if not emotions:
            return {"error": "No emotion data provided"}

        # 提取PAD维度数据
        valence_data = [e.valence for e in emotions]
        arousal_data = [e.arousal for e in emotions]

        # 创建二维直方图
        heatmap, xedges, yedges = np.histogram2d(
            valence_data, arousal_data,
            bins=[20, 20],
            range=[[-1, 1], [-1, 1]]
        )

        return {
            "heatmap": heatmap.tolist(),
            "xedges": xedges.tolist(),
            "yedges": yedges.tolist(),
            "xlabel": "Valence (愉悦度)",
            "ylabel": "Arousal (唤醒度)",
            "title": "情绪状态分布热力图"
        }

    @staticmethod
    def create_emotion_timeline_data(emotions: List[EmotionProfile]) -> Dict[str, Any]:
        """创建情绪时间线数据"""
        if not emotions:
            return {"error": "No emotion data provided"}

        timeline_data = {
            "timestamps": [e.timestamp for e in emotions if e.timestamp],
            "valence": [e.valence for e in emotions],
            "arousal": [e.arousal for e in emotions],
            "dominance": [e.dominance for e in emotions],
            "joy": [e.joy for e in emotions],
            "sadness": [e.sadness for e in emotions],
            "anger": [e.anger for e in emotions],
            "fear": [e.fear for e in emotions],
            "intensity": [e.intensity for e in emotions],
            "primary_emotions": [e.get_primary_emotion() for e in emotions]
        }

        return timeline_data

    @staticmethod
    def create_emotion_radar_data(emotion: EmotionProfile) -> Dict[str, Any]:
        """创建情绪雷达图数据"""
        # 选择主要的情绪维度进行雷达图展示
        dimensions = {
            "愉悦度": max(0, emotion.valence),  # 只显示正值
            "唤醒度": max(0, emotion.arousal),
            "支配感": max(0, emotion.dominance),
            "快乐": max(0, emotion.joy),
            "悲伤": max(0, emotion.sadness),
            "愤怒": max(0, emotion.anger),
            "恐惧": max(0, emotion.fear),
            "信任": (emotion.trust + 1) / 2,  # 归一化到0-1
            "焦虑": max(0, emotion.anxiety)
        }

        return {
            "dimensions": dimensions,
            "title": "情绪雷达图",
            "description": f"情绪强度: {emotion.intensity:.2f}, 主要情绪: {emotion.get_primary_emotion()}"
        }

    @staticmethod
    def analyze_emotion_patterns(emotions: List[EmotionProfile]) -> Dict[str, Any]:
        """分析情绪模式"""
        if len(emotions) < 3:
            return {"error": "需要至少3个情绪样本"}

        analysis = {
            "overall_trends": {},
            "emotion_clusters": {},
            "stability_analysis": {},
            "mood_transitions": {}
        }

        # 计算总体趋势
        for dim in ["valence", "arousal", "joy", "sadness", "anger", "fear"]:
            values = [getattr(e, dim) for e in emotions]
            trend = np.polyfit(range(len(values)), values, 1)[0]  # 线性趋势
            analysis["overall_trends"][dim] = {
                "slope": trend,
                "direction": "increasing" if trend > 0.01 else "decreasing" if trend < -0.01 else "stable"
            }

        # 情绪稳定性分析
        pad_values = [[e.valence, e.arousal, e.dominance] for e in emotions]
        stability_scores = []

        for i in range(1, len(pad_values)):
            prev = np.array(pad_values[i-1])
            curr = np.array(pad_values[i])
            stability = 1 - np.linalg.norm(curr - prev) / np.sqrt(3)
            stability_scores.append(stability)

        analysis["stability_analysis"] = {
            "average_stability": np.mean(stability_scores),
            "stability_trend": np.polyfit(range(len(stability_scores)), stability_scores, 1)[0],
            "most_stable_period": max(range(len(stability_scores)), key=lambda i: stability_scores[i]),
            "least_stable_period": min(range(len(stability_scores)), key=lambda i: stability_scores[i])
        }

        # 情绪转变分析
        transitions = []
        for i in range(1, len(emotions)):
            prev_primary = emotions[i-1].get_primary_emotion()
            curr_primary = emotions[i].get_primary_emotion()

            if prev_primary != curr_primary:
                change_magnitude = abs(emotions[i].valence - emotions[i-1].valence) + abs(emotions[i].arousal - emotions[i-1].arousal)
                transitions.append({
                    "from": prev_primary,
                    "to": curr_primary,
                    "magnitude": change_magnitude,
                    "step": i
                })

        # 找出最常见的转变
        transition_counts = {}
        for t in transitions:
            key = f"{t['from']}->{t['to']}"
            transition_counts[key] = transition_counts.get(key, 0) + 1

        analysis["mood_transitions"] = {
            "total_transitions": len(transitions),
            "most_common_transition": max(transition_counts.items(), key=lambda x: x[1]) if transition_counts else None,
            "transition_frequency": len(transitions) / (len(emotions) - 1),
            "significant_transitions": [t for t in transitions if t["magnitude"] > 0.5]
        }

        return analysis

    @staticmethod
    def generate_emotion_report(emotions: List[EmotionProfile], agent_id: str = "Agent") -> str:
        """生成情绪分析报告"""
        if not emotions:
            return "无情绪数据可供分析"

        report = []
        report.append(f"=== {agent_id} 情绪分析报告 ===")
        report.append(f"分析样本数: {len(emotions)}")
        report.append("")

        # 总体情绪统计
        avg_emotion = EmotionProfile()
        for emotion in emotions:
            avg_emotion.valence += emotion.valence
            avg_emotion.arousal += emotion.arousal
            avg_emotion.joy += emotion.joy
            avg_emotion.sadness += emotion.sadness
            avg_emotion.anger += emotion.anger
            avg_emotion.fear += emotion.fear

        n = len(emotions)
        avg_emotion.valence /= n
        avg_emotion.arousal /= n
        avg_emotion.joy /= n
        avg_emotion.sadness /= n
        avg_emotion.anger /= n
        avg_emotion.fear /= n

        report.append("总体情绪状态:")
        report.append(f"  平均愉悦度: {avg_emotion.valence:+.3f}")
        report.append(f"  平均唤醒度: {avg_emotion.arousal:+.3f}")
        report.append(f"  平均快乐: {avg_emotion.joy:+.3f}")
        report.append(f"  平均悲伤: {avg_emotion.sadness:+.3f}")
        report.append(f"  平均愤怒: {avg_emotion.anger:+.3f}")
        report.append(f"  平均恐惧: {avg_emotion.fear:+.3f}")
        report.append("")

        # 情绪分布
        primary_emotions = [e.get_primary_emotion() for e in emotions]
        emotion_counts = {}
        for emotion in primary_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        report.append("情绪分布:")
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(emotions)) * 100
            report.append(f"  {emotion}: {count} 次 ({percentage:.1f}%)")
        report.append("")

        # 情绪动态分析
        if len(emotions) >= 3:
            patterns = EmotionAnalytics.analyze_emotion_patterns(emotions)

            report.append("情绪动态分析:")
            for dim, trend in patterns["overall_trends"].items():
                if trend["slope"] > 0.01:
                    report.append(f"  {dim}: 呈上升趋势")
                elif trend["slope"] < -0.01:
                    report.append(f"  {dim}: 呈下降趋势")
                else:
                    report.append(f"  {dim}: 相对稳定")

            stability = patterns["stability_analysis"]["average_stability"]
            report.append(f"  情绪稳定性: {stability:.3f} ({'高' if stability > 0.7 else '中' if stability > 0.4 else '低'})")
            report.append("")

        # 当前情绪状态
        current_emotion = emotions[-1]
        report.append("当前情绪状态:")
        report.append(f"  主要情绪: {current_emotion.get_primary_emotion()}")
        report.append(f"  情绪描述: {current_emotion.get_mood_description()}")
        report.append(f"  情绪强度: {current_emotion.intensity:.3f}")
        report.append(f"  情绪象限: {current_emotion.get_emotion_quadrant()}")

        return "\n".join(report)


# 演示函数：展示新的情绪系统功能
def demonstrate_emotion_system():
    """演示新的情绪系统功能"""
    print("=== 情绪系统演示 ===\n")

    # 1. 创建各种情绪画像
    print("1. 创建情绪画像示例:")
    emotions = [
        EmotionProfile(valence=0.8, arousal=0.7, joy=0.9, context="非常开心"),
        EmotionProfile(valence=-0.6, arousal=0.8, anger=0.8, sadness=0.4, context="愤怒悲伤"),
        EmotionProfile(valence=-0.3, arousal=-0.2, dominance=-0.4, anxiety=0.6, context="焦虑不安"),
        EmotionProfile(valence=0.2, arousal=0.3, trust=0.7, gratitude=0.5, context="信任感激")
    ]

    for i, emotion in enumerate(emotions, 1):
        print(f"  情绪 {i}: {emotion.get_mood_description()}")
        print(f"    主要情绪: {emotion.get_primary_emotion()}")
        print(f"    强度: {emotion.intensity:.3f}")
        print(f"    象限: {emotion.get_emotion_quadrant()}")
        print()

    # 2. 情绪相似性和混合演示
    print("2. 情绪相似性和混合:")
    emotion1 = EmotionProfile(valence=0.8, joy=0.9, context="开心")
    emotion2 = EmotionProfile(valence=0.7, joy=0.8, context="快乐")

    similarity = emotion1.similarity(emotion2)
    print(f"  相似度: {similarity:.3f}")

    blended = emotion1.blend_with(emotion2, 0.5)
    print(f"  混合情绪: {blended.get_mood_description()}")
    print()

    # 3. 情绪生成演示
    print("3. 情绪生成演示:")
    context = "在公园里看到朋友，感觉很开心"
    personality = {"description": "乐观外向的人"}

    generated_emotion = EmotionGenerator.generate_from_context(context, personality)
    print(f"  上下文: {context}")
    print(f"  人格: {personality['description']}")
    print(f"  生成情绪: {generated_emotion.get_mood_description()}")
    print(f"  愉悦度: {generated_emotion.valence:.3f}")
    print()

    # 4. 情绪演化演示
    print("4. 情绪演化演示:")
    current_emotion = EmotionProfile(valence=0.2, arousal=0.3, context="平静")
    new_context = "突然遇到惊喜的事情"

    evolved_emotion = EmotionGenerator.evolve_emotion(current_emotion, new_context, personality)
    print(f"  当前情绪: {current_emotion.get_mood_description()}")
    print(f"  新上下文: {new_context}")
    print(f"  演化后情绪: {evolved_emotion.get_mood_description()}")
    print()

    # 5. 情绪分析演示
    print("5. 情绪分析演示:")
    report = EmotionAnalytics.generate_emotion_report(emotions, "演示智能体")
    print(report)
    print()

    # 6. 可视化数据演示
    print("6. 可视化数据生成:")
    heatmap_data = EmotionAnalytics.create_emotion_heatmap_data(emotions)
    print(f"  热力图数据点数: {len(heatmap_data.get('heatmap', []))}")

    timeline_data = EmotionAnalytics.create_emotion_timeline_data(emotions)
    print(f"  时间线数据点数: {len(timeline_data.get('valence', []))}")

    radar_data = EmotionAnalytics.create_emotion_radar_data(emotions[0])
    print(f"  雷达图维度数: {len(radar_data.get('dimensions', {}))}")
    print()

    print("=== 演示完成 ===")


if __name__ == "__main__":
    demonstrate_emotion_system()

