import unittest
import os
import sys

# 添加 src 目录到模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# 修改导入语句
from data_structures import PowerPoint, Slide, SlideContent


class TestDataStructuresAdvanced(unittest.TestCase):
    """
    测试 PowerPoint 数据结构的高级特性，主要关注：
    1. __str__ 方法的输出格式
    2. 复杂的多级项目符号
    3. 边界情况处理
    """

    def setUp(self):
        # 创建测试用的复杂幻灯片内容
        self.complex_bullet_points = [
            {'text': "一级标题", 'level': 0},
            {'text': "二级内容1", 'level': 1},
            {'text': "三级内容A", 'level': 2},
            {'text': "三级内容B", 'level': 2},
            {'text': "二级内容2", 'level': 1},
        ]

        self.slide_content = SlideContent(
            title="复杂幻灯片",
            bullet_points=self.complex_bullet_points,
            image_path="images/complex.png"
        )

    def test_str_output_format(self):
        """测试 PowerPoint __str__ 方法的输出格式"""
        slide = Slide(layout_id=1, layout_name="复杂布局", content=self.slide_content)
        ppt = PowerPoint(title="格式测试", slides=[slide])

        expected_output = """PowerPoint Presentation: 格式测试

Slide 1:
  Title: 复杂幻灯片
  Layout: 复杂布局 (ID: 1)
  Bullet Points:
- 一级标题
  - 二级内容1
    - 三级内容A
    - 三级内容B
  - 二级内容2
  Image: images/complex.png"""

        self.assertEqual(str(ppt), expected_output)

    def test_empty_presentation(self):
        """测试空演示文稿的处理"""
        ppt = PowerPoint(title="空演示文稿")
        self.assertEqual(str(ppt), "PowerPoint Presentation: 空演示文稿")

    def test_mixed_content_slides(self):
        """测试混合内容的幻灯片"""
        # 只有标题的幻灯片
        title_only = SlideContent(title="仅标题")

        # 有标题和图片的幻灯片
        title_image = SlideContent(
            title="标题和图片",
            image_path="images/test.png"
        )

        # 有标题和项目符号的幻灯片
        title_bullets = SlideContent(
            title="标题和要点",
            bullet_points=[{'text': "要点1", 'level': 0}]
        )

        slides = [
            Slide(layout_id=1, layout_name="标题布局", content=title_only),
            Slide(layout_id=2, layout_name="图片布局", content=title_image),
            Slide(layout_id=3, layout_name="内容布局", content=title_bullets)
        ]

        ppt = PowerPoint(title="混合内容测试", slides=slides)

        # 验证幻灯片数量
        self.assertEqual(len(ppt.slides), 3)

        # 验证每个幻灯片的特定属性
        self.assertIsNone(ppt.slides[0].content.image_path)
        self.assertEqual(ppt.slides[1].content.image_path, "images/test.png")
        self.assertEqual(len(ppt.slides[2].content.bullet_points), 1)

    def test_bullet_points_structure(self):
        """测试项目符号的结构完整性"""
        for bullet_point in self.complex_bullet_points:
            # 验证每个项目符号都有必要的键
            self.assertIn('text', bullet_point)
            self.assertIn('level', bullet_point)
            # 验证层级值的合法性
            self.assertGreaterEqual(bullet_point['level'], 0)
            self.assertLess(bullet_point['level'], 3)  # 假设最大支持3级
            # 验证文本非空
            self.assertTrue(bullet_point['text'].strip())


if __name__ == '__main__':
    unittest.main()
