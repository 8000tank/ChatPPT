import os
from input_parser import parse_input_text
from ppt_generator import generate_presentation
from template_manager import load_template, get_layout_mapping, print_layouts

def main():
    input_text = """
    # ChatPPT_Demo2(LGBTQIA)

    ## ChatPPT Demo2 LGBTQIA [Title]

    ## Right Pattern Content [Right Pattern Content]
    - Right Pattern Content 1
    - Right Pattern Content 2
    
    ## Overview [Overview]
    - Overview 1
    - Overview 2
    
    ## Chart Slide [Chart Slide]
    - Chart Slide 1
    - Chart Slide 2
    
    ## Left Pattern Content [Left Pattern Content]
    - Left Pattern Content 1
    - Left Pattern Content 2
    
    ## Smart Art [Smart Art]
    - Smart Art 1
    - Smart Art 2
            
    ## Two Photo Content [Two Photo Content]
    - Two Photo Content 1
    ![Two Photo Content 2](images/forecast.png)
    ![Two Photo Content 1](images/performance_chart.png)
    
    ## Right Pattern Content Blue title [Right Pattern Content Blue title]
    - Right Pattern Content Blue title 1
    - Right Pattern Content Blue title 2
    
    ## Questions [Questions]
    - Questions 1
    - Questions 2    
    
    ## Left Pattern Content Orange Title [Left Pattern Content Orange Title]
    - Left Pattern Content Orange Title 1
    - Left Pattern Content Orange Title 2    
    """

    template_file = 'templates/LGBTQIA Pride Month presentation.pptx'
    prs = load_template(template_file)

    print("Available Slide Layouts:")
    print_layouts(prs)

    layout_mapping = get_layout_mapping(prs)

    powerpoint_data, presentation_title = parse_input_text(input_text, layout_mapping)

    output_pptx = f"outputs/{presentation_title}.pptx"
    
    # 添加以下代码来创建 outputs 目录（如果不存在）
    os.makedirs(os.path.dirname(output_pptx), exist_ok=True)
    
    generate_presentation(powerpoint_data, template_file, output_pptx)

if __name__ == "__main__":
    main()
