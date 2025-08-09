from flask import Flask, render_template, request, Response
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        model_name = request.form.get('model_name', 'Model1')
        duration = int(request.form.get('duration', 30)) * 1000  # Convert seconds to ms
        effect_type = request.form.get('effect_type', 'On')

        # Generate basic xLights sequence XML dynamically
        root = ET.Element('xrgb', version='2024.05', showDir='.')
        
        timing_grids = ET.SubElement(root, 'timingGrids')
        timing_grid = ET.SubElement(timing_grids, 'timingGrid', saveID='0', type='FREQ', name='New Timing', lengthMS=str(duration), spacing='50', visibility='1')
        
        display_elements = ET.SubElement(root, 'displayElements')
        display_element = ET.SubElement(display_elements, 'displayElement', name=model_name, type='model', visibility='1')
        
        effects = ET.SubElement(root, 'effects')
        effect_layer = ET.SubElement(effects, 'effectLayer', timing='0')
        effect_settings = f"E_CHECKBOX_{effect_type}_RampUp=0,E_SLIDER_{effect_type}_RampUp=0,E_CHECKBOX_{effect_type}_RampDown=0,E_SLIDER_{effect_type}_RampDown=0,E_CHECKBOX_{effect_type}_Background=0"
        effect = ET.SubElement(effect_layer, 'effect', ref='0', type=effect_type, startTime='0', endTime=str(duration), intensity='100', palette='C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#000000', settings=effect_settings)
        
        xml_content = ET.tostring(root, encoding='unicode', method='xml')
        
        return Response(xml_content, mimetype='text/xml', headers={"Content-Disposition": "attachment; filename=generated_sequence.xml"})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
