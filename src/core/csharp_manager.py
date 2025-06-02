#!/usr/bin/env python3
"""
Менеджер C# проектів для RimWorld Mod Builder
Створення та управління C# кодом для модів RimWorld
"""

import os
from pathlib import Path
from jinja2 import Template

class CSharpManager:
    """Клас для управління C# проектами RimWorld модів"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.assemblies_path = self.project_path / "Assemblies"
        self.source_path = self.project_path / "Source"
        
    def create_csharp_structure(self, mod_name, author):
        """Створення структури C# проекту"""
        try:
            # Створення папок
            self.assemblies_path.mkdir(exist_ok=True)
            self.source_path.mkdir(exist_ok=True)
            
            project_source_path = self.source_path / mod_name
            project_source_path.mkdir(exist_ok=True)
            
            # Створення .csproj файлу
            self.create_csproj_file(mod_name, project_source_path)
            
            # Створення базових C# файлів
            self.create_mod_class(mod_name, author, project_source_path)
            self.create_harmony_patches(mod_name, project_source_path)
            
            # Створення build скрипту
            self.create_build_script(mod_name)
            
            return True
            
        except Exception as e:
            print(f"Помилка створення C# структури: {e}")
            return False
            
    def create_csproj_file(self, mod_name, project_path):
        """Створення .csproj файлу для RimWorld мода"""
        csproj_template = '''<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net472</TargetFramework>
    <AssemblyName>{{ mod_name }}</AssemblyName>
    <RootNamespace>{{ mod_name }}</RootNamespace>
    <OutputPath>..\\..\\Assemblies\\</OutputPath>
    <AppendTargetFrameworkToOutputPath>false</AppendTargetFrameworkToOutputPath>
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>
    <Optimize>true</Optimize>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Krafs.Rimworld.Ref" Version="1.5.4104" />
    <PackageReference Include="Lib.Harmony" Version="2.2.2" />
  </ItemGroup>

  <ItemGroup>
    <Reference Include="0Harmony">
      <HintPath>$(RimWorldInstallDir)\\Mods\\Harmony\\Current\\Assemblies\\0Harmony.dll</HintPath>
      <Private>False</Private>
    </Reference>
  </ItemGroup>

</Project>'''

        template = Template(csproj_template)
        content = template.render(mod_name=mod_name)
        
        csproj_file = project_path / f"{mod_name}.csproj"
        csproj_file.write_text(content, encoding='utf-8')
        
    def create_mod_class(self, mod_name, author, project_path):
        """Створення основного класу мода"""
        mod_class_template = '''using Verse;
using HarmonyLib;

namespace {{ mod_name }}
{
    /// <summary>
    /// Основний клас мода {{ mod_name }}
    /// Автор: {{ author }}
    /// </summary>
    public class {{ mod_name }}Mod : Mod
    {
        public {{ mod_name }}Mod(ModContentPack content) : base(content)
        {
            // Ініціалізація Harmony
            var harmony = new Harmony("{{ author.lower() }}.{{ mod_name.lower() }}");
            harmony.PatchAll();
            
            Log.Message("[{{ mod_name }}] Мод успішно завантажено!");
        }
    }
}'''

        template = Template(mod_class_template)
        content = template.render(
            mod_name=mod_name,
            author=author
        )
        
        mod_file = project_path / f"{mod_name}Mod.cs"
        mod_file.write_text(content, encoding='utf-8')
        
    def create_harmony_patches(self, mod_name, project_path):
        """Створення прикладу Harmony патчів"""
        patches_template = '''using HarmonyLib;
using Verse;
using RimWorld;

namespace {{ mod_name }}.Patches
{
    /// <summary>
    /// Приклад Harmony патчу
    /// </summary>
    [HarmonyPatch(typeof(Game), "InitNewGame")]
    public static class Game_InitNewGame_Patch
    {
        /// <summary>
        /// Постфікс для методу InitNewGame
        /// Викликається після ініціалізації нової гри
        /// </summary>
        [HarmonyPostfix]
        public static void Postfix()
        {
            Log.Message("[{{ mod_name }}] Нова гра ініціалізована з модом!");
        }
    }
    
    /// <summary>
    /// Приклад префікс патчу
    /// </summary>
    [HarmonyPatch(typeof(Pawn), "GetGizmos")]
    public static class Pawn_GetGizmos_Patch
    {
        /// <summary>
        /// Префікс для методу GetGizmos
        /// Дозволяє змінити поведінку до виконання оригінального методу
        /// </summary>
        [HarmonyPrefix]
        public static bool Prefix(Pawn __instance)
        {
            // Повертаємо true для продовження виконання оригінального методу
            // Повертаємо false для пропуску оригінального методу
            return true;
        }
    }
}'''

        template = Template(patches_template)
        content = template.render(mod_name=mod_name)
        
        patches_dir = project_path / "Patches"
        patches_dir.mkdir(exist_ok=True)
        
        patches_file = patches_dir / "ExamplePatches.cs"
        patches_file.write_text(content, encoding='utf-8')
        
    def create_build_script(self, mod_name):
        """Створення скрипту збірки"""
        build_script_template = '''@echo off
echo Building {{ mod_name }}...

cd Source\\{{ mod_name }}
dotnet build --configuration Release

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Assembly saved to Assemblies\\{{ mod_name }}.dll
) else (
    echo Build failed!
    pause
)

pause'''

        template = Template(build_script_template)
        content = template.render(mod_name=mod_name)
        
        build_file = self.project_path / "build.bat"
        build_file.write_text(content, encoding='utf-8')
        
    def get_csharp_templates(self):
        """Отримання шаблонів C# класів"""
        return {
            'ThingComp': self.get_thingcomp_template(),
            'JobDriver': self.get_jobdriver_template(),
            'Hediff': self.get_hediff_template(),
            'MapComponent': self.get_mapcomponent_template(),
            'GameComponent': self.get_gamecomponent_template(),
            'DefOf': self.get_defof_template()
        }
        
    def get_thingcomp_template(self):
        """Шаблон для ThingComp класу"""
        return '''using Verse;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Компонент для предметів
    /// </summary>
    public class {{ class_name }} : ThingComp
    {
        public {{ class_name }}Properties Props => ({{ class_name }}Properties)props;
        
        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            // Ініціалізація після створення
        }
        
        public override void CompTick()
        {
            base.CompTick();
            // Логіка кожен тік (60 разів на секунду)
        }
        
        public override void PostExposeData()
        {
            base.PostExposeData();
            // Збереження/завантаження даних
        }
    }
    
    /// <summary>
    /// Властивості компонента
    /// </summary>
    public class {{ class_name }}Properties : CompProperties
    {
        public {{ class_name }}Properties()
        {
            compClass = typeof({{ class_name }});
        }
    }
}'''

    def get_jobdriver_template(self):
        """Шаблон для JobDriver класу"""
        return '''using System.Collections.Generic;
using Verse;
using Verse.AI;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Драйвер роботи для пешаків
    /// </summary>
    public class {{ class_name }} : JobDriver
    {
        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            // Резервування ресурсів перед початком роботи
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }
        
        protected override IEnumerable<Toil> MakeNewToils()
        {
            // Перевірки перед початком роботи
            this.FailOnDespawnedNullOrForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);
            
            // Йти до цілі
            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.Touch);
            
            // Виконати дію
            yield return new Toil
            {
                initAction = delegate
                {
                    // Логіка виконання роботи
                    DoWork();
                },
                defaultCompleteMode = ToilCompleteMode.Instant
            };
        }
        
        private void DoWork()
        {
            // Реалізація роботи
        }
    }
}'''

    def get_hediff_template(self):
        """Шаблон для Hediff класу"""
        return '''using Verse;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Ефект здоров'я (хвороба, травма, імплант тощо)
    /// </summary>
    public class {{ class_name }} : Hediff
    {
        public override void PostAdd(DamageInfo? dinfo)
        {
            base.PostAdd(dinfo);
            // Логіка після додавання ефекту
        }
        
        public override void PostRemoved()
        {
            base.PostRemoved();
            // Логіка після видалення ефекту
        }
        
        public override void Tick()
        {
            base.Tick();
            // Логіка кожен тік
        }
        
        public override bool ShouldRemove => false; // Умова видалення
        
        public override string LabelInBrackets => "{{ label }}"; // Мітка в дужках
    }
}'''

    def get_mapcomponent_template(self):
        """Шаблон для MapComponent класу"""
        return '''using Verse;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Компонент карти для зберігання даних на рівні карти
    /// </summary>
    public class {{ class_name }} : MapComponent
    {
        public {{ class_name }}(Map map) : base(map)
        {
        }
        
        public override void MapComponentTick()
        {
            base.MapComponentTick();
            // Логіка кожен тік карти
        }
        
        public override void ExposeData()
        {
            base.ExposeData();
            // Збереження/завантаження даних карти
        }
    }
}'''

    def get_gamecomponent_template(self):
        """Шаблон для GameComponent класу"""
        return '''using Verse;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Компонент гри для зберігання глобальних даних
    /// </summary>
    public class {{ class_name }} : GameComponent
    {
        public {{ class_name }}(Game game)
        {
        }
        
        public override void GameComponentTick()
        {
            base.GameComponentTick();
            // Логіка кожен тік гри
        }
        
        public override void ExposeData()
        {
            base.ExposeData();
            // Збереження/завантаження глобальних даних
        }
    }
}'''

    def get_defof_template(self):
        """Шаблон для DefOf класу"""
        return '''using Verse;
using RimWorld;

namespace {{ namespace }}
{
    /// <summary>
    /// Статичні посилання на дефініції
    /// </summary>
    [DefOf]
    public static class {{ class_name }}
    {
        // Приклади посилань на дефініції
        public static ThingDef {{ thing_def_name }};
        public static JobDef {{ job_def_name }};
        public static ResearchProjectDef {{ research_def_name }};
        
        static {{ class_name }}()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof({{ class_name }}));
        }
    }
}'''

    def create_csharp_file(self, template_name, class_name, namespace, file_path):
        """Створення C# файлу з шаблону"""
        templates = self.get_csharp_templates()
        
        if template_name not in templates:
            raise ValueError(f"Невідомий шаблон: {template_name}")
            
        template = Template(templates[template_name])
        content = template.render(
            class_name=class_name,
            namespace=namespace,
            label=class_name.lower(),
            thing_def_name=f"My{class_name}Thing",
            job_def_name=f"My{class_name}Job",
            research_def_name=f"My{class_name}Research"
        )
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        return True
