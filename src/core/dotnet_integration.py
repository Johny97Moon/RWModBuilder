#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Інтеграція з .NET Framework для RimWorld Mod Builder v2.0.1
Підтримка C# компонентів, компіляції та .NET бібліотек
"""

import os
import sys
import subprocess
import json
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    from utils.simple_logger import get_logger_instance
except ImportError:
    def get_logger_instance():
        class Logger:
            def get_logger(self): 
                class L:
                    def info(self, m): print(f"INFO: {m}")
                    def error(self, m): print(f"ERROR: {m}")
                    def warning(self, m): print(f"WARNING: {m}")
                    def debug(self, m): print(f"DEBUG: {m}")
                return L()
        return Logger()


class DotNetEnvironment:
    """Клас для роботи з .NET середовищем"""
    
    def __init__(self):
        self.logger = get_logger_instance().get_logger()
        self.dotnet_path = None
        self.msbuild_path = None
        self.framework_versions = []
        self.sdk_versions = []
        
        self._detect_environment()
    
    def _detect_environment(self):
        """Виявлення .NET середовища"""
        try:
            # Пошук dotnet CLI
            self.dotnet_path = self._find_executable("dotnet")
            if self.dotnet_path:
                self.logger.info(f"✅ Знайдено dotnet CLI: {self.dotnet_path}")
                self._get_sdk_versions()
            
            # Пошук MSBuild
            self.msbuild_path = self._find_msbuild()
            if self.msbuild_path:
                self.logger.info(f"✅ Знайдено MSBuild: {self.msbuild_path}")
            
            # Виявлення Framework версій
            self._detect_framework_versions()
            
        except Exception as e:
            self.logger.error(f"Помилка виявлення .NET середовища: {e}")
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Пошук виконуваного файлу"""
        try:
            result = subprocess.run(
                ["where" if os.name == "nt" else "which", name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')[0]
        except:
            return None
    
    def _find_msbuild(self) -> Optional[str]:
        """Пошук MSBuild"""
        possible_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Спроба через dotnet
        if self.dotnet_path:
            try:
                result = subprocess.run(
                    [self.dotnet_path, "msbuild", "--version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return f"{self.dotnet_path} msbuild"
            except:
                pass
        
        return None
    
    def _get_sdk_versions(self):
        """Отримання версій SDK"""
        if not self.dotnet_path:
            return
        
        try:
            result = subprocess.run(
                [self.dotnet_path, "--list-sdks"],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    version = line.split()[0]
                    self.sdk_versions.append(version)
            
            self.logger.info(f"✅ Знайдено .NET SDK версії: {', '.join(self.sdk_versions)}")
            
        except Exception as e:
            self.logger.warning(f"Не вдалося отримати версії SDK: {e}")
    
    def _detect_framework_versions(self):
        """Виявлення версій .NET Framework"""
        try:
            # Перевірка через реєстр Windows
            if os.name == "nt":
                import winreg
                
                framework_key = r"SOFTWARE\Microsoft\NET Framework Setup\NDP"
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, framework_key) as key:
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                if subkey_name.startswith("v"):
                                    self.framework_versions.append(subkey_name)
                                i += 1
                            except WindowsError:
                                break
                except:
                    pass
            
            # Перевірка через dotnet
            if self.dotnet_path:
                try:
                    result = subprocess.run(
                        [self.dotnet_path, "--list-runtimes"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    for line in result.stdout.strip().split('\n'):
                        if "Microsoft.NETCore.App" in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                version = parts[1]
                                if version not in self.framework_versions:
                                    self.framework_versions.append(f"Core {version}")
                
                except:
                    pass
            
            if self.framework_versions:
                self.logger.info(f"✅ Знайдено .NET Framework версії: {', '.join(self.framework_versions)}")
            
        except Exception as e:
            self.logger.warning(f"Не вдалося виявити версії Framework: {e}")
    
    def is_available(self) -> bool:
        """Перевірка доступності .NET середовища"""
        return self.dotnet_path is not None or self.msbuild_path is not None
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Отримання інформації про середовище"""
        return {
            "dotnet_available": self.dotnet_path is not None,
            "dotnet_path": self.dotnet_path,
            "msbuild_available": self.msbuild_path is not None,
            "msbuild_path": self.msbuild_path,
            "sdk_versions": self.sdk_versions,
            "framework_versions": self.framework_versions,
            "is_ready": self.is_available()
        }


class CSharpCompiler:
    """Компілятор C# коду для RimWorld модів"""
    
    def __init__(self, dotnet_env: DotNetEnvironment):
        self.dotnet_env = dotnet_env
        self.logger = get_logger_instance().get_logger()
        
        # Шляхи до RimWorld бібліотек
        self.rimworld_libs = self._find_rimworld_libs()
    
    def _find_rimworld_libs(self) -> List[str]:
        """Пошук бібліотек RimWorld"""
        possible_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed",
            r"C:\Program Files\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed",
            r"D:\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed",
            r"E:\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                libs = []
                for file in os.listdir(path):
                    if file.endswith('.dll'):
                        libs.append(os.path.join(path, file))
                
                if libs:
                    self.logger.info(f"✅ Знайдено RimWorld бібліотеки: {path}")
                    return libs
        
        self.logger.warning("⚠️ RimWorld бібліотеки не знайдено")
        return []
    
    def create_csharp_project(self, project_name: str, output_dir: str) -> str:
        """Створення C# проєкту для RimWorld мода"""
        project_dir = os.path.join(output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Створення .csproj файлу
        csproj_content = self._generate_csproj(project_name)
        csproj_path = os.path.join(project_dir, f"{project_name}.csproj")
        
        with open(csproj_path, 'w', encoding='utf-8') as f:
            f.write(csproj_content)
        
        # Створення базового C# файлу
        cs_content = self._generate_base_cs(project_name)
        cs_path = os.path.join(project_dir, f"{project_name}.cs")
        
        with open(cs_path, 'w', encoding='utf-8') as f:
            f.write(cs_content)
        
        self.logger.info(f"✅ C# проєкт створено: {project_dir}")
        return project_dir
    
    def _generate_csproj(self, project_name: str) -> str:
        """Генерація .csproj файлу"""
        return f'''<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <Import Project="$(MSBuildExtensionsPath)\\$(MSBuildToolsVersion)\\Microsoft.Common.props" Condition="Exists('$(MSBuildExtensionsPath)\\$(MSBuildToolsVersion)\\Microsoft.Common.props')" />
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Debug</Configuration>
    <Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
    <ProjectGuid>{{12345678-1234-1234-1234-123456789012}}</ProjectGuid>
    <OutputType>Library</OutputType>
    <AppDesignerFolder>Properties</AppDesignerFolder>
    <RootNamespace>{project_name}</RootNamespace>
    <AssemblyName>{project_name}</AssemblyName>
    <TargetFrameworkVersion>v4.7.2</TargetFrameworkVersion>
    <FileAlignment>512</FileAlignment>
    <Deterministic>true</Deterministic>
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)|$(Platform)' == 'Debug|AnyCPU' ">
    <DebugSymbols>true</DebugSymbols>
    <DebugType>full</DebugType>
    <Optimize>false</Optimize>
    <OutputPath>bin\\Debug\\</OutputPath>
    <DefineConstants>DEBUG;TRACE</DefineConstants>
    <ErrorReport>prompt</ErrorReport>
    <WarningLevel>4</WarningLevel>
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)|$(Platform)' == 'Release|AnyCPU' ">
    <DebugType>pdbonly</DebugType>
    <Optimize>true</Optimize>
    <OutputPath>bin\\Release\\</OutputPath>
    <DefineConstants>TRACE</DefineConstants>
    <ErrorReport>prompt</ErrorReport>
    <WarningLevel>4</WarningLevel>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System" />
    <Reference Include="System.Core" />
    <Reference Include="System.Xml.Linq" />
    <Reference Include="System.Data.DataSetExtensions" />
    <Reference Include="Microsoft.CSharp" />
    <Reference Include="System.Data" />
    <Reference Include="System.Net.Http" />
    <Reference Include="System.Xml" />
    <!-- RimWorld References -->
    <Reference Include="Assembly-CSharp">
      <HintPath>$(RimWorldPath)\\RimWorldWin64_Data\\Managed\\Assembly-CSharp.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="UnityEngine.CoreModule">
      <HintPath>$(RimWorldPath)\\RimWorldWin64_Data\\Managed\\UnityEngine.CoreModule.dll</HintPath>
      <Private>False</Private>
    </Reference>
    <Reference Include="0Harmony">
      <HintPath>$(RimWorldPath)\\RimWorldWin64_Data\\Managed\\0Harmony.dll</HintPath>
      <Private>False</Private>
    </Reference>
  </ItemGroup>
  <ItemGroup>
    <Compile Include="{project_name}.cs" />
    <Compile Include="Properties\\AssemblyInfo.cs" />
  </ItemGroup>
  <Import Project="$(MSBuildToolsPath)\\Microsoft.CSharp.targets" />
</Project>'''
    
    def _generate_base_cs(self, project_name: str) -> str:
        """Генерація базового C# файлу"""
        return f'''using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Verse;
using RimWorld;
using HarmonyLib;

namespace {project_name}
{{
    [StaticConstructorOnStartup]
    public static class {project_name}Mod
    {{
        static {project_name}Mod()
        {{
            Log.Message("[{project_name}] Mod loaded successfully!");
            
            // Ініціалізація Harmony
            var harmony = new Harmony("{project_name.lower()}.mod");
            harmony.PatchAll();
        }}
    }}
    
    // Приклад Harmony патчу
    [HarmonyPatch(typeof(Game), "InitNewGame")]
    public static class Game_InitNewGame_Patch
    {{
        public static void Postfix()
        {{
            Log.Message("[{project_name}] New game initialized!");
        }}
    }}
}}'''
    
    def compile_project(self, project_path: str, configuration: str = "Release") -> Tuple[bool, str]:
        """Компіляція C# проєкту"""
        if not self.dotnet_env.is_available():
            return False, "❌ .NET середовище недоступне"
        
        try:
            # Використання MSBuild
            if self.dotnet_env.msbuild_path:
                cmd = [
                    self.dotnet_env.msbuild_path if not self.dotnet_env.msbuild_path.endswith("msbuild") 
                    else self.dotnet_env.dotnet_path,
                ]
                
                if self.dotnet_env.msbuild_path.endswith("msbuild"):
                    cmd.append("msbuild")
                
                cmd.extend([
                    project_path,
                    f"/p:Configuration={configuration}",
                    "/p:Platform=AnyCPU",
                    "/verbosity:minimal"
                ])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(project_path)
                )
                
                if result.returncode == 0:
                    self.logger.info(f"✅ Проєкт скомпільовано успішно: {project_path}")
                    return True, "✅ Компіляція успішна"
                else:
                    error_msg = result.stderr or result.stdout
                    self.logger.error(f"❌ Помилка компіляції: {error_msg}")
                    return False, f"❌ Помилка компіляції: {error_msg}"
            
            return False, "❌ MSBuild недоступний"
            
        except Exception as e:
            error_msg = f"❌ Виняток під час компіляції: {e}"
            self.logger.error(error_msg)
            return False, error_msg


class RimWorldModTemplate:
    """Генератор шаблонів RimWorld модів"""
    
    def __init__(self):
        self.logger = get_logger_instance().get_logger()
    
    def create_mod_structure(self, mod_name: str, output_dir: str, include_csharp: bool = True) -> str:
        """Створення повної структури мода"""
        mod_dir = os.path.join(output_dir, mod_name)
        
        # Створення папок
        folders = [
            "About",
            "Defs",
            "Textures",
            "Patches",
            "Languages/English/Keyed",
            "Languages/English/DefInjected"
        ]
        
        if include_csharp:
            folders.extend([
                "Source",
                "Assemblies"
            ])
        
        for folder in folders:
            os.makedirs(os.path.join(mod_dir, folder), exist_ok=True)
        
        # Створення About.xml
        self._create_about_xml(mod_dir, mod_name)
        
        # Створення базових файлів
        self._create_base_files(mod_dir, mod_name)
        
        if include_csharp:
            # Створення C# проєкту
            dotnet_env = DotNetEnvironment()
            if dotnet_env.is_available():
                compiler = CSharpCompiler(dotnet_env)
                source_dir = os.path.join(mod_dir, "Source")
                compiler.create_csharp_project(mod_name, source_dir)
        
        self.logger.info(f"✅ Структура мода створена: {mod_dir}")
        return mod_dir
    
    def _create_about_xml(self, mod_dir: str, mod_name: str):
        """Створення About.xml"""
        about_content = f'''<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <packageId>author.{mod_name.lower().replace(' ', '')}</packageId>
    <name>{mod_name}</name>
    <author>Your Name</author>
    <description>Description of {mod_name} mod.</description>
    <supportedVersions>
        <li>1.4</li>
    </supportedVersions>
    <modDependencies>
        <!-- Add dependencies here -->
    </modDependencies>
    <loadAfter>
        <!-- Add load order here -->
    </loadAfter>
</ModMetaData>'''
        
        with open(os.path.join(mod_dir, "About", "About.xml"), 'w', encoding='utf-8') as f:
            f.write(about_content)
    
    def _create_base_files(self, mod_dir: str, mod_name: str):
        """Створення базових файлів"""
        # Приклад ThingDef
        thingdef_content = f'''<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <!-- Example ThingDef for {mod_name} -->
    <!--
    <ThingDef ParentName="ResourceBase">
        <defName>{mod_name}Resource</defName>
        <label>{mod_name.lower()} resource</label>
        <description>A resource from {mod_name} mod.</description>
        <graphicData>
            <texPath>Things/Item/Resource/{mod_name}Resource</texPath>
            <graphicClass>Graphic_Single</graphicClass>
        </graphicData>
        <statBases>
            <MarketValue>10</MarketValue>
            <Mass>0.5</Mass>
        </statBases>
        <thingCategories>
            <li>ResourcesRaw</li>
        </thingCategories>
    </ThingDef>
    -->
</Defs>'''
        
        with open(os.path.join(mod_dir, "Defs", "ThingDefs.xml"), 'w', encoding='utf-8') as f:
            f.write(thingdef_content)
        
        # Приклад Keyed файлу
        keyed_content = f'''<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
    <!-- Translations for {mod_name} -->
    <!-- Example: -->
    <!-- <{mod_name}ResourceLabel>{mod_name} Resource</{mod_name}ResourceLabel> -->
</LanguageData>'''
        
        with open(os.path.join(mod_dir, "Languages", "English", "Keyed", f"{mod_name}.xml"), 'w', encoding='utf-8') as f:
            f.write(keyed_content)


# Глобальний екземпляр
_dotnet_env = None

def get_dotnet_environment() -> DotNetEnvironment:
    """Отримання глобального екземпляра .NET середовища"""
    global _dotnet_env
    if _dotnet_env is None:
        _dotnet_env = DotNetEnvironment()
    return _dotnet_env


if __name__ == "__main__":
    # Тестування .NET інтеграції
    print("🔧 Тестування .NET інтеграції...")
    
    env = get_dotnet_environment()
    info = env.get_environment_info()
    
    print(f"✅ .NET доступний: {info['is_ready']}")
    print(f"📍 dotnet CLI: {info['dotnet_path']}")
    print(f"🔨 MSBuild: {info['msbuild_path']}")
    print(f"📦 SDK версії: {', '.join(info['sdk_versions'])}")
    print(f"🏗️ Framework версії: {', '.join(info['framework_versions'])}")
    
    if env.is_available():
        # Тест створення проєкту
        template = RimWorldModTemplate()
        test_mod = template.create_mod_structure("TestMod", "./test_output", include_csharp=True)
        print(f"✅ Тестовий мод створено: {test_mod}")
