Vuelve a tu página de Login (http://localhost:5173/).

Escribe:

Usuario: jperez

Contraseña: miclave123

Dale a Iniciar Sesión.







1\. Para el Backend (Python/FastAPI)

Abre una terminal y ejecuta estos comandos uno por uno:



bash



cd D:\\Maestria\\Modulo 6\\CMMS\\CMMS\\backend

python -m uvicorn main:app --reload

(El servidor quedará corriendo en el puerto 8000).



2\. Para el Frontend (Vue/Vite)

Abre una nueva terminal (no cierres la anterior) y ejecuta:



bash



cd D:\\Maestria\\Modulo 6\\CMMS\\CMMS\\frontend

npm run dev

(El servidor quedará corriendo en el puerto 5173).







\---



\## 🔹 Pasos para restaurar tu proyecto desde GitHub



1\. \*\*Verifica que tienes el remoto configurado\*\*  

&#x20;  ```bash

&#x20;  git remote -v

&#x20;  ```

&#x20;  Debes ver algo como:

&#x20;  ```

&#x20;  origin  https://github.com/khitisakamachisa-collab/cmmsbioai.git (fetch)

&#x20;  origin  https://github.com/khitisakamachisa-collab/cmmsbioai.git (push)

&#x20;  ```



2\. \*\*Descarga la última versión desde GitHub\*\*  

&#x20;  ```bash

&#x20;  git fetch origin

&#x20;  ```



3\. \*\*Restablece tu rama local `main` al estado remoto\*\*  

&#x20;  ⚠️ Esto descarta todos los cambios locales no subidos.

&#x20;  ```bash

&#x20;  git reset --hard origin/main

&#x20;  ```



4\. \*\*Confirma que tu rama está sincronizada\*\*  

&#x20;  ```bash

&#x20;  git status

&#x20;  ```

&#x20;  Debe mostrar:  

&#x20;  ```

&#x20;  On branch main

&#x20;  Your branch is up to date with 'origin/main'.

&#x20;  nothing to commit, working tree clean

&#x20;  ```



\---



\## 🔹 Alternativa (si prefieres clonar limpio)

Si tu carpeta local está muy desordenada, puedes borrar el proyecto y clonar de nuevo:



```bash

git clone https://github.com/khitisakamachisa-collab/cmmsbioai.git

```



Esto te dará una copia fresca exactamente como está en GitHub.



\---



👉 Con esto tu proyecto quedará \*\*exactamente en el último commit que subiste a GitHub\*\*.  



