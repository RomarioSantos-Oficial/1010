# Base 3D da Luna

Esta pasta contém uma base técnica adulta, gerada localmente para continuar a
produção do avatar. Ela já é um corpo inteiro animável, mas ainda não reproduz
fielmente o rosto nem as proporções finais das referências da Luna.

Arquivos:

- `luna_base_v0_1.blend`: projeto editável no Blender com corpo, rig e cena de prévia;
- `luna_base_v0_1.glb`: exportação portátil do corpo rigado e das âncoras das mãos;
- `luna_base_v0_1_preview.png`: inspeção visual frontal da base;
- `luna_base_v0_1_report.json`: contagens e estado verificável do ativo.

Capacidades já presentes:

- corpo adulto completo, incluindo mãos e pés;
- esqueleto com 163 ossos e pesos de deformação;
- 38 ossos detectados para dedos e metacarpos;
- âncoras `Luna_LeftHand_Grip` e `Luna_RightHand_Grip` para segurar produtos.

Pendências antes de chamar o avatar de final: escultura de identidade baseada no
turntable, retopologia, blendshapes faciais, ajuste das roupas, mapeamento humanoide
VRM 1.0 e testes de animação/colisão. Explicações sobre produtos adultos continuam
protegidas pela verificação de idade da aplicação; o arquivo 3D não remove essa regra.

Para reconstruir o ativo, execute `scripts/build_luna_3d_base.py` com o Blender
portátil instalado em `tools/blender` e com as extensões oficiais MPFB e VRM ativas.
