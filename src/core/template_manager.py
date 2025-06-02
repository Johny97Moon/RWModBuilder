#!/usr/bin/env python3
"""
Менеджер шаблонів для RimWorld Mod Builder
Управління та використання шаблонів дефініцій
"""

import os
from pathlib import Path
from jinja2 import Template
import json

class TemplateManager:
    """Клас для управління шаблонами дефініцій"""
    
    def __init__(self, templates_dir="templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        self.load_templates()
        
    def load_templates(self):
        """Завантаження всіх шаблонів з папки templates"""
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            self.create_default_templates()
            
        for template_file in self.templates_dir.glob("*.xml"):
            template_name = template_file.stem
            try:
                content = template_file.read_text(encoding='utf-8')
                self.templates[template_name] = {
                    'content': content,
                    'path': template_file,
                    'description': self.extract_description(content)
                }
            except Exception as e:
                print(f"Помилка завантаження шаблону {template_name}: {e}")
                
    def extract_description(self, content):
        """Витягування опису з коментарів шаблону"""
        lines = content.split('\n')
        for line in lines:
            if '<!-- Description:' in line:
                return line.split('Description:')[1].split('-->')[0].strip()
        return "Опис недоступний"
        
    def get_template_list(self):
        """Отримання списку доступних шаблонів"""
        return [
            {
                'name': name,
                'description': data['description'],
                'category': self.get_template_category(name)
            }
            for name, data in self.templates.items()
        ]
        
    def get_template_category(self, template_name):
        """Визначення категорії шаблону"""
        categories = {
            'about': 'Основні',
            'thingdef': 'Предмети',
            'recipedef': 'Рецепти',
            'researchprojectdef': 'Дослідження',
            'pawnkinddef': 'Персонажі',
            'traitdef': 'Риси',
            'factiondef': 'Фракції',
            'biomedef': 'Біоми',
            'jobdef': 'Роботи',
            'workgiverdef': 'Робочі місця'
        }
        
        for key, category in categories.items():
            if key in template_name.lower():
                return category
        return 'Інші'
        
    def render_template(self, template_name, variables):
        """Рендеринг шаблону з заданими змінними"""
        if template_name not in self.templates:
            raise ValueError(f"Шаблон {template_name} не знайдено")
            
        template_content = self.templates[template_name]['content']
        template = Template(template_content)
        
        try:
            return template.render(**variables)
        except Exception as e:
            raise ValueError(f"Помилка рендерингу шаблону: {e}")
            
    def create_default_templates(self):
        """Створення шаблонів за замовчуванням"""
        default_templates = {
            'about_template.xml': '''<!-- Description: Базовий шаблон для About.xml -->
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>{{ mod_name }}</name>
    <author>{{ author }}</author>
    <packageId>{{ package_id }}</packageId>
    <description>{{ description }}</description>
    <supportedVersions>
        <li>1.5</li>
    </supportedVersions>
    {% if dependencies %}
    <modDependencies>
        {% for dep in dependencies %}
        <li>
            <packageId>{{ dep.package_id }}</packageId>
            <displayName>{{ dep.name }}</displayName>
        </li>
        {% endfor %}
    </modDependencies>
    {% endif %}
</ModMetaData>''',

            'thingdef_template.xml': '''<!-- Description: Шаблон для створення предметів та будівель -->
<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <ThingDef>
        <defName>{{ def_name }}</defName>
        <label>{{ label }}</label>
        <description>{{ description }}</description>
        <thingClass>{{ thing_class|default('Thing') }}</thingClass>
        <category>{{ category|default('Item') }}</category>
        <tickerType>{{ ticker_type|default('Never') }}</tickerType>
        <altitudeLayer>{{ altitude_layer|default('Item') }}</altitudeLayer>
        <passability>{{ passability|default('PassThroughOnly') }}</passability>
        <pathCost>{{ path_cost|default('14') }}</pathCost>
        <useHitPoints>{{ use_hit_points|default('true') }}</useHitPoints>
        <selectable>{{ selectable|default('true') }}</selectable>
        <drawGUIOverlay>{{ draw_gui_overlay|default('true') }}</drawGUIOverlay>
        <rotatable>{{ rotatable|default('false') }}</rotatable>
        <fillPercent>{{ fill_percent|default('0.40') }}</fillPercent>
        <statBases>
            <MaxHitPoints>{{ max_hit_points|default('100') }}</MaxHitPoints>
            <WorkToBuild>{{ work_to_build|default('1000') }}</WorkToBuild>
            <Flammability>{{ flammability|default('1.0') }}</Flammability>
            {% if beauty %}
            <Beauty>{{ beauty }}</Beauty>
            {% endif %}
        </statBases>
        {% if cost_list %}
        <costList>
            {% for cost in cost_list %}
            <{{ cost.material }}>{{ cost.amount }}</{{ cost.material }}>
            {% endfor %}
        </costList>
        {% endif %}
        <graphicData>
            <texPath>{{ texture_path }}</texPath>
            <graphicClass>{{ graphic_class|default('Graphic_Single') }}</graphicClass>
            {% if draw_size %}
            <drawSize>{{ draw_size }}</drawSize>
            {% endif %}
        </graphicData>
        {% if research_prerequisites %}
        <researchPrerequisites>
            {% for research in research_prerequisites %}
            <li>{{ research }}</li>
            {% endfor %}
        </researchPrerequisites>
        {% endif %}
    </ThingDef>
</Defs>''',

            'recipedef_template.xml': '''<!-- Description: Шаблон для створення рецептів крафту -->
<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <RecipeDef>
        <defName>{{ def_name }}</defName>
        <label>{{ label }}</label>
        <description>{{ description }}</description>
        <jobString>{{ job_string|default('Виготовлення ' + label) }}</jobString>
        <workSpeedStat>{{ work_speed_stat|default('GeneralLaborSpeed') }}</workSpeedStat>
        <workSkill>{{ work_skill|default('Crafting') }}</workSkill>
        <effectWorking>{{ effect_working|default('Cook') }}</effectWorking>
        <soundWorking>{{ sound_working|default('Recipe_CookMeal') }}</soundWorking>
        <workAmount>{{ work_amount|default('1000') }}</workAmount>
        <unfinishedThingDef>{{ unfinished_thing_def|default('UnfinishedComponent') }}</unfinishedThingDef>
        {% if ingredients %}
        <ingredients>
            {% for ingredient in ingredients %}
            <li>
                <filter>
                    <thingDefs>
                        <li>{{ ingredient.thing_def }}</li>
                    </thingDefs>
                </filter>
                <count>{{ ingredient.count }}</count>
            </li>
            {% endfor %}
        </ingredients>
        {% endif %}
        <products>
            <{{ product_def }}>{{ product_count|default('1') }}</{{ product_def }}>
        </products>
        {% if recipe_users %}
        <recipeUsers>
            {% for user in recipe_users %}
            <li>{{ user }}</li>
            {% endfor %}
        </recipeUsers>
        {% endif %}
        {% if research_prerequisite %}
        <researchPrerequisite>{{ research_prerequisite }}</researchPrerequisite>
        {% endif %}
        {% if skill_requirements %}
        <skillRequirements>
            {% for skill in skill_requirements %}
            <{{ skill.name }}>{{ skill.level }}</{{ skill.name }}>
            {% endfor %}
        </skillRequirements>
        {% endif %}
    </RecipeDef>
</Defs>''',

            'researchprojectdef_template.xml': '''<!-- Description: Шаблон для створення проектів досліджень -->
<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <ResearchProjectDef>
        <defName>{{ def_name }}</defName>
        <label>{{ label }}</label>
        <description>{{ description }}</description>
        <baseCost>{{ base_cost|default('1000') }}</baseCost>
        <techLevel>{{ tech_level|default('Industrial') }}</techLevel>
        {% if prerequisites %}
        <prerequisites>
            {% for prereq in prerequisites %}
            <li>{{ prereq }}</li>
            {% endfor %}
        </prerequisites>
        {% endif %}
        {% if research_view_x and research_view_y %}
        <researchViewX>{{ research_view_x }}</researchViewX>
        <researchViewY>{{ research_view_y }}</researchViewY>
        {% endif %}
        {% if required_research_building %}
        <requiredResearchBuilding>{{ required_research_building }}</requiredResearchBuilding>
        {% endif %}
        {% if required_research_facilities %}
        <requiredResearchFacilities>
            {% for facility in required_research_facilities %}
            <li>{{ facility }}</li>
            {% endfor %}
        </requiredResearchFacilities>
        {% endif %}
    </ResearchProjectDef>
</Defs>'''
        }
        
        for filename, content in default_templates.items():
            template_file = self.templates_dir / filename
            if not template_file.exists():
                template_file.write_text(content, encoding='utf-8')
                
    def save_template(self, name, content, description=""):
        """Збереження нового шаблону"""
        if description:
            content = f"<!-- Description: {description} -->\n{content}"
            
        template_file = self.templates_dir / f"{name}.xml"
        template_file.write_text(content, encoding='utf-8')
        
        self.templates[name] = {
            'content': content,
            'path': template_file,
            'description': description or self.extract_description(content)
        }
        
    def delete_template(self, name):
        """Видалення шаблону"""
        if name in self.templates:
            template_file = self.templates[name]['path']
            if template_file.exists():
                template_file.unlink()
            del self.templates[name]
            
    def get_template_variables(self, template_name):
        """Отримання списку змінних шаблону"""
        if template_name not in self.templates:
            return []

        content = self.templates[template_name]['content']
        template = Template(content)

        # Простий спосіб знайти змінні в шаблоні
        import re
        variables = re.findall(r'\{\{\s*(\w+)', content)
        return list(set(variables))  # Унікальні змінні

    def get_available_templates(self):
        """Отримання словника доступних шаблонів"""
        return self.templates

    def get_template_content(self, template_name):
        """Отримання вмісту шаблону"""
        if template_name in self.templates:
            return self.templates[template_name]['content']
        return None
