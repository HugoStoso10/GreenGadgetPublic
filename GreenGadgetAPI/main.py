#----------------------------------------------------------------------------
#   API do projeto (vai permitir a comunicação entre os vários elementos do projeto)
#
#   Bibliotecas: fastapi; "uvicorn[standard]"; "psycopg[binary]"; passlib[bcrypt];
#                pydantic[email]; requests; python-multipart;
#
#   Comando para por a API a correr:
#       python -m uvicorn main:app --reload
#
#----------------------------------------------------------------------------

# Bibliotecas
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from psycopg.errors import UniqueViolation

from pathlib import Path
import uuid


#----------------------------------------------------------------------------
# Funções de ficheiros
#----------------------------------------------------------------------------

from db import get_connection
from auth import criar_hash_password, verificar_password
from ipma import atualizar_previsoes_ipma


#----------------------------------------------------------------------------
# CONFIGURAÇÃO
#----------------------------------------------------------------------------

app = FastAPI(
    title="GreenGadget API",
    description="API principal da aplicação GreenGadget",
    version="1.0.0"
)


#----------------------------------------------------------------------------
# CORS
# Permite que apps/frontend comuniquem com a API
#----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
        # Em produção podes trocar por:
        # "https://teu-dominio.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#----------------------------------------------------------------------------
# MODELOS
#----------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AddDeviceRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    user_id: int


class UpdateDeviceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    plant_id: int


class SensorDataRequest(BaseModel):
    device_code: str = Field(min_length=1, max_length=50)
    temperature: float
    air_humidity: float
    soil_humidity: float

class AddWateringDeviceRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    user_id: int
    device_id: int

class UpdateWateringDeviceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    device_id: int

class ManualWateringCommandRequest(BaseModel):
    duration_seconds: int = Field(
        default=5,
        ge=1,
        le=600
    )
    reason: str = Field(
        default="manual",
        min_length=1,
        max_length=100
    )

#----------------------------------------------------------------------------
# ROOT / STATUS
#----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "success": True,
        "message": "GreenGadget API"
    }


@app.get("/status")
def status():
    return {
        "success": True,
        "message": "API online"
    }


#----------------------------------------------------------------------------
# REGISTO
#----------------------------------------------------------------------------

@app.post("/register")
def register_user(data: RegisterRequest):

    name = data.name.strip()
    email = data.email.strip().lower()
    password = data.password

    password_hash = criar_hash_password(password)

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, password_hash)
                )

        return {
            "success": True,
            "message": "Conta criada com sucesso."
        }

    except UniqueViolation:

        return {
            "success": False,
            "message": "Este e-mail já está registado."
        }

    except Exception as erro:

        print("Erro no register:", erro)

        return {
            "success": False,
            "message": "Erro ao criar conta."
        }


#----------------------------------------------------------------------------
# LOGIN
#----------------------------------------------------------------------------

@app.post("/login")
def login_user(data: LoginRequest):

    email = data.email.strip().lower()
    password = data.password

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, name, email, password_hash
                    FROM users
                    WHERE email = %s
                    """,
                    (email,)
                )

                user = cur.fetchone()

        if not user:

            return {
                "success": False,
                "message": "E-mail ou palavra-passe inválidos."
            }

        user_id, name, email, password_hash = user

        if not verificar_password(password, password_hash):

            return {
                "success": False,
                "message": "E-mail ou palavra-passe inválidos."
            }

        return {
            "success": True,
            "message": "Login efetuado com sucesso.",
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }

    except Exception as erro:

        print("Erro no login:", erro)

        return {
            "success": False,
            "message": "Erro ao fazer login."
        }


#----------------------------------------------------------------------------
# DISPOSITIVOS
#----------------------------------------------------------------------------

#----------------------------------------------------------------------------
# Associar um dispositivo já registado a um utilizador
#----------------------------------------------------------------------------

@app.post("/devices/add")
def add_device(data: AddDeviceRequest):

    code = data.code.strip()

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # Verificar se o utilizador existe
                cur.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE id = %s
                    """,
                    (data.user_id,)
                )

                user = cur.fetchone()

                if not user:

                    return {
                        "success": False,
                        "message": "Utilizador não encontrado."
                    }


                # Procurar dispositivo pelo código
                cur.execute(
                    """
                    SELECT id, name, user_id
                    FROM devices
                    WHERE code = %s
                    """,
                    (code,)
                )

                device = cur.fetchone()

                if not device:

                    return {
                        "success": False,
                        "message": "Dispositivo não encontrado."
                    }


                device_id, device_name, current_user_id = device


                # Verificar se já está associado
                if current_user_id is not None:

                    return {
                        "success": False,
                        "message": "Este dispositivo já está associado a um utilizador."
                    }


                # Associar dispositivo
                cur.execute(
                    """
                    UPDATE devices
                    SET user_id = %s
                    WHERE id = %s
                    """,
                    (data.user_id, device_id)
                )


        return {
            "success": True,
            "message": "Dispositivo associado com sucesso.",
            "device": {
                "id": device_id,
                "name": device_name,
                "code": code
            }
        }

    except Exception as erro:

        print("Erro ao adicionar dispositivo:", erro)

        return {
            "success": False,
            "message": "Erro ao associar dispositivo."
        }


#----------------------------------------------------------------------------
# VERIFICAR DISPOSITIVO PELO CÓDIGO
#----------------------------------------------------------------------------

@app.get("/devices/code/{code}")
def get_device_by_code(code: str):

    code = code.strip()

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        code,
                        name,
                        user_id,
                        plant_id,
                        image_path,
                        created_at
                    FROM devices
                    WHERE code = %s
                    """,
                    (code,)
                )

                device = cur.fetchone()

        if not device:

            return {
                "success": False,
                "message": "Dispositivo não encontrado."
            }

        (
            device_id,
            device_code,
            device_name,
            user_id,
            plant_id,
            image_path,
            created_at
        ) = device

        return {
            "success": True,
            "message": "Dispositivo encontrado.",
            "device": {
                "id": device_id,
                "code": device_code,
                "name": device_name,
                "user_id": user_id,
                "plant_id": plant_id,
                "image_path": image_path,
                "created_at": created_at
            }
        }

    except Exception as erro:

        print("Erro ao procurar dispositivo pelo código:", erro)

        return {
            "success": False,
            "message": "Erro ao procurar dispositivo."
        }


#----------------------------------------------------------------------------
# LISTAR DISPOSITIVOS DE UM UTILIZADOR
#----------------------------------------------------------------------------

@app.get("/devices/{user_id}")
def get_devices(user_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        code,
                        name,
                        plant_id,
                        image_path,
                        created_at
                    FROM devices
                    WHERE user_id = %s
                    ORDER BY id
                    """,
                    (user_id,)
                )

                devices = cur.fetchall()


        resultado = []

        for device in devices:

            device_id, code, name, plant_id, image_path, created_at = device

            resultado.append({
                "id": device_id,
                "code": code,
                "name": name,
                "plant_id": plant_id,
                "image_path": image_path,
                "created_at": created_at
            })


        return {
            "success": True,
            "devices": resultado
        }

    except Exception as erro:

        print("Erro ao obter dispositivos:", erro)

        return {
            "success": False,
            "message": "Erro ao obter dispositivos."
        }


#----------------------------------------------------------------------------
# OBTER UM DISPOSITIVO ESPECÍFICO
#----------------------------------------------------------------------------

@app.get("/device/{device_id}")
def get_device(device_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        code,
                        name,
                        user_id,
                        plant_id,
                        image_path,
                        created_at
                    FROM devices
                    WHERE id = %s
                    """,
                    (device_id,)
                )

                device = cur.fetchone()


        if not device:

            return {
                "success": False,
                "message": "Dispositivo não encontrado."
            }


        (
            device_id,
            code,
            name,
            user_id,
            plant_id,
            image_path,
            created_at
        ) = device


        return {
            "success": True,
            "device": {
                "id": device_id,
                "code": code,
                "name": name,
                "user_id": user_id,
                "plant_id": plant_id,
                "image_path": image_path,
                "created_at": created_at
            }
        }

    except Exception as erro:

        print("Erro ao obter dispositivo:", erro)

        return {
            "success": False,
            "message": "Erro ao obter dispositivo."
        }


#----------------------------------------------------------------------------
# ALTERAR CONFIGURAÇÕES DO DISPOSITIVO
#----------------------------------------------------------------------------

@app.put("/devices/{device_id}")
def update_device(device_id: int, data: UpdateDeviceRequest):

    name = data.name.strip()

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # Verificar se o dispositivo existe
                cur.execute(
                    """
                    SELECT id
                    FROM devices
                    WHERE id = %s
                    """,
                    (device_id,)
                )

                device = cur.fetchone()

                if not device:

                    return {
                        "success": False,
                        "message": "Dispositivo não encontrado."
                    }


                # Verificar se a planta existe
                cur.execute(
                    """
                    SELECT id
                    FROM plants
                    WHERE id = %s
                    """,
                    (data.plant_id,)
                )

                plant = cur.fetchone()

                if not plant:

                    return {
                        "success": False,
                        "message": "Planta não encontrada."
                    }


                # Atualizar dispositivo
                cur.execute(
                    """
                    UPDATE devices
                    SET name = %s,
                        plant_id = %s
                    WHERE id = %s
                    """,
                    (name, data.plant_id, device_id)
                )


        return {
            "success": True,
            "message": "Dispositivo atualizado com sucesso."
        }

    except Exception as erro:

        print("Erro ao atualizar dispositivo:", erro)

        return {
            "success": False,
            "message": "Erro ao atualizar dispositivo."
        }


#----------------------------------------------------------------------------
# DESASSOCIAR DISPOSITIVO
#----------------------------------------------------------------------------

@app.delete("/devices/{device_id}/association")
def remove_device(device_id: int, user_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # Verificar se o dispositivo existe
                cur.execute(
                    """
                    SELECT id, user_id
                    FROM devices
                    WHERE id = %s
                    """,
                    (device_id,)
                )

                device = cur.fetchone()

                if not device:

                    return {
                        "success": False,
                        "message": "Dispositivo não encontrado."
                    }


                current_device_id, current_user_id = device


                # Verificar se está associado
                if current_user_id is None:

                    return {
                        "success": False,
                        "message": "Este dispositivo não está associado a nenhum utilizador."
                    }


                # Verificar se pertence ao utilizador
                if current_user_id != user_id:

                    return {
                        "success": False,
                        "message": "Este dispositivo não pertence a este utilizador."
                    }


                # Remover associação
                cur.execute(
                    """
                    UPDATE devices
                    SET user_id = NULL
                    WHERE id = %s
                    """,
                    (device_id,)
                )


        return {
            "success": True,
            "message": "Dispositivo desassociado com sucesso."
        }

    except Exception as erro:

        print("Erro ao desassociar dispositivo:", erro)

        return {
            "success": False,
            "message": "Erro ao desassociar dispositivo."
        }


#----------------------------------------------------------------------------
# ALTERAR IMAGEM DO DISPOSITIVO
#----------------------------------------------------------------------------

@app.post("/devices/{device_id}/image")
async def update_device_image(
    device_id: int,
    image: UploadFile = File(...)
):

    try:

        # Verificar se o dispositivo existe
        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id
                    FROM devices
                    WHERE id = %s
                    """,
                    (device_id,)
                )

                device = cur.fetchone()


        if not device:

            return {
                "success": False,
                "message": "Dispositivo não encontrado."
            }


        # Verificar tipo de ficheiro
        tipos_permitidos = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]

        if image.content_type not in tipos_permitidos:

            return {
                "success": False,
                "message": "Formato de imagem não suportado."
            }


        # Criar pasta das imagens
        pasta_imagens = Path("uploads/devices")
        pasta_imagens.mkdir(parents=True, exist_ok=True)


        # Definir extensão
        extensoes = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }

        extensao = extensoes[image.content_type]


        # Criar nome único
        nome_ficheiro = f"{device_id}_{uuid.uuid4().hex}{extensao}"

        caminho = pasta_imagens / nome_ficheiro


        # Guardar imagem
        conteudo = await image.read()

        with open(caminho, "wb") as ficheiro:

            ficheiro.write(conteudo)


        # Caminho guardado na BD
        image_path = str(caminho).replace("\\", "/")


        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE devices
                    SET image_path = %s
                    WHERE id = %s
                    """,
                    (image_path, device_id)
                )


        return {
            "success": True,
            "message": "Imagem atualizada com sucesso.",
            "image_path": image_path
        }

    except Exception as erro:

        print("Erro ao atualizar imagem:", erro)

        return {
            "success": False,
            "message": "Erro ao atualizar imagem."
        }


#----------------------------------------------------------------------------
# DADOS DOS SENSORES
#----------------------------------------------------------------------------

# Endpoint utilizado pelo ESP32
@app.post("/devices/data")
def receive_sensor_data(data: SensorDataRequest):

    device_code = data.device_code.strip()

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # Procurar dispositivo
                cur.execute(
                    """
                    SELECT id
                    FROM devices
                    WHERE code = %s
                    """,
                    (device_code,)
                )

                device = cur.fetchone()

                if not device:

                    return {
                        "success": False,
                        "message": "Dispositivo não encontrado."
                    }


                device_id = device[0]


                # Guardar dados dos sensores
                cur.execute(
                    """
                    INSERT INTO sensor_data (
                        device_id,
                        temperature,
                        air_humidity,
                        soil_humidity
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        device_id,
                        data.temperature,
                        data.air_humidity,
                        data.soil_humidity
                    )
                )


        return {
            "success": True,
            "message": "Dados dos sensores guardados com sucesso."
        }

    except Exception as erro:

        print("Erro ao guardar dados dos sensores:", erro)

        return {
            "success": False,
            "message": "Erro ao guardar dados dos sensores."
        }


#----------------------------------------------------------------------------
# OBTER DADOS DOS SENSORES DE UM DISPOSITIVO
#----------------------------------------------------------------------------

@app.get("/devices/{device_id}/data")
def get_device_data(device_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        timestamp,
                        temperature,
                        air_humidity,
                        soil_humidity
                    FROM sensor_data
                    WHERE device_id = %s
                    ORDER BY timestamp DESC
                    """,
                    (device_id,)
                )

                data = cur.fetchall()


        resultado = []

        for row in data:

            sensor_id, timestamp, temperature, air_humidity, soil_humidity = row

            resultado.append({
                "id": sensor_id,
                "timestamp": timestamp,
                "temperature": temperature,
                "air_humidity": air_humidity,
                "soil_humidity": soil_humidity
            })


        return {
            "success": True,
            "device_id": device_id,
            "data": resultado
        }

    except Exception as erro:

        print("Erro ao obter dados dos sensores:", erro)

        return {
            "success": False,
            "message": "Erro ao obter dados dos sensores."
        }


# ============================================================
# WATERING DEVICES
# ============================================================

@app.post("/watering-devices/add")
def add_watering_device(request: AddWateringDeviceRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar utilizador
        cur.execute(
            "SELECT id FROM users WHERE id = %s",
            (request.user_id,)
        )
        user = cur.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Utilizador não encontrado."
            )

        # Procurar módulo de rega pelo código
        cur.execute(
            """
            SELECT id, user_id, device_id
            FROM watering_devices
            WHERE code = %s
            """,
            (request.code,)
        )
        watering_device = cur.fetchone()

        if not watering_device:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        watering_device_id, existing_user_id, existing_device_id = watering_device

        # Verificar se já está associado
        if existing_user_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Este módulo de rega já está associado."
            )

        # Verificar dispositivo de sensores
        cur.execute(
            """
            SELECT id, user_id
            FROM devices
            WHERE id = %s
            """,
            (request.device_id,)
        )
        device = cur.fetchone()

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Dispositivo de sensores não encontrado."
            )

        device_id, device_user_id = device

        # O dispositivo tem de pertencer ao mesmo utilizador
        if device_user_id != request.user_id:
            raise HTTPException(
                status_code=403,
                detail="O dispositivo não pertence a este utilizador."
            )

        # Verificar se o dispositivo já tem módulo de rega
        cur.execute(
            """
            SELECT id
            FROM watering_devices
            WHERE device_id = %s
            """,
            (request.device_id,)
        )

        existing_watering = cur.fetchone()

        if existing_watering:
            raise HTTPException(
                status_code=400,
                detail="Este dispositivo já tem um módulo de rega associado."
            )

        # Associar módulo ao utilizador e ao dispositivo
        cur.execute(
            """
            UPDATE watering_devices
            SET user_id = %s,
                device_id = %s
            WHERE id = %s
            RETURNING id, code, name, user_id, device_id, created_at
            """,
            (
                request.user_id,
                request.device_id,
                watering_device_id
            )
        )

        result = cur.fetchone()

        conn.commit()

        return {
            "success": True,
            "message": "Módulo de rega associado com sucesso.",
            "watering_device": {
                "id": result[0],
                "code": result[1],
                "name": result[2],
                "user_id": result[3],
                "device_id": result[4],
                "created_at": result[5]
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao associar módulo de rega: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.get("/watering-devices/{user_id}")
def get_watering_devices(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                wd.id,
                wd.code,
                wd.name,
                wd.user_id,
                wd.device_id,
                wd.created_at,
                d.name AS device_name,
                d.plant_id
            FROM watering_devices wd
            LEFT JOIN devices d
                ON wd.device_id = d.id
            WHERE wd.user_id = %s
            ORDER BY wd.id
            """,
            (user_id,)
        )

        rows = cur.fetchall()

        watering_devices = []

        for row in rows:
            watering_devices.append({
                "id": row[0],
                "code": row[1],
                "name": row[2],
                "user_id": row[3],
                "device_id": row[4],
                "created_at": row[5],
                "device_name": row[6],
                "plant_id": row[7]
            })

        return {
            "success": True,
            "watering_devices": watering_devices
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter módulos de rega: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.get("/watering-devices/code/{code}")
def get_watering_device_by_code(code: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                code,
                name,
                user_id,
                device_id,
                created_at
            FROM watering_devices
            WHERE code = %s
            """,
            (code,)
        )

        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        return {
            "success": True,
            "watering_device": {
                "id": row[0],
                "code": row[1],
                "name": row[2],
                "user_id": row[3],
                "device_id": row[4],
                "created_at": row[5]
            }
        }

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.get("/watering-device/{watering_device_id}")
def get_watering_device(watering_device_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                wd.id,
                wd.code,
                wd.name,
                wd.user_id,
                wd.device_id,
                wd.created_at,
                d.name AS device_name,
                d.plant_id
            FROM watering_devices wd
            LEFT JOIN devices d
                ON wd.device_id = d.id
            WHERE wd.id = %s
            """,
            (watering_device_id,)
        )

        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        return {
            "success": True,
            "watering_device": {
                "id": row[0],
                "code": row[1],
                "name": row[2],
                "user_id": row[3],
                "device_id": row[4],
                "created_at": row[5],
                "device_name": row[6],
                "plant_id": row[7]
            }
        }

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.put("/watering-devices/{watering_device_id}")
def update_watering_device(
    watering_device_id: int,
    request: UpdateWateringDeviceRequest
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar módulo
        cur.execute(
            """
            SELECT id, user_id
            FROM watering_devices
            WHERE id = %s
            """,
            (watering_device_id,)
        )

        watering_device = cur.fetchone()

        if not watering_device:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        user_id = watering_device[1]

        # Verificar dispositivo
        cur.execute(
            """
            SELECT id, user_id
            FROM devices
            WHERE id = %s
            """,
            (request.device_id,)
        )

        device = cur.fetchone()

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Dispositivo não encontrado."
            )

        if device[1] != user_id:
            raise HTTPException(
                status_code=403,
                detail="O dispositivo não pertence ao utilizador."
            )

        # Verificar se outro módulo já usa este dispositivo
        cur.execute(
            """
            SELECT id
            FROM watering_devices
            WHERE device_id = %s
              AND id != %s
            """,
            (
                request.device_id,
                watering_device_id
            )
        )

        duplicate = cur.fetchone()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Este dispositivo já está associado a outro módulo de rega."
            )

        cur.execute(
            """
            UPDATE watering_devices
            SET name = %s,
                device_id = %s
            WHERE id = %s
            RETURNING id, code, name, user_id, device_id, created_at
            """,
            (
                request.name,
                request.device_id,
                watering_device_id
            )
        )

        result = cur.fetchone()

        conn.commit()

        return {
            "success": True,
            "message": "Módulo de rega atualizado com sucesso.",
            "watering_device": {
                "id": result[0],
                "code": result[1],
                "name": result[2],
                "user_id": result[3],
                "device_id": result[4],
                "created_at": result[5]
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar módulo de rega: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.delete("/watering-devices/{watering_device_id}/association")
def delete_watering_device_association(
    watering_device_id: int,
    user_id: int
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT user_id
            FROM watering_devices
            WHERE id = %s
            """,
            (watering_device_id,)
        )

        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        if row[0] != user_id:
            raise HTTPException(
                status_code=403,
                detail="Este módulo não pertence ao utilizador."
            )

        cur.execute(
            """
            UPDATE watering_devices
            SET user_id = NULL,
                device_id = NULL
            WHERE id = %s
            """,
            (watering_device_id,)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Módulo de rega desassociado com sucesso."
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao desassociar módulo de rega: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


# ============================================================
# COMANDO DE REGA — USADO PELO ESP32
# ============================================================

@app.get("/watering-devices/code/{code}/command")
def get_watering_command(code: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar módulo
        cur.execute(
            """
            SELECT id
            FROM watering_devices
            WHERE code = %s
            """,
            (code,)
        )

        device = cur.fetchone()

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        watering_device_id = device[0]

        # Procurar o comando pendente mais antigo
        cur.execute(
            """
            SELECT
                id,
                watering_device_id,
                duration_seconds,
                reason,
                status,
                created_at
            FROM watering_commands
            WHERE watering_device_id = %s
              AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (watering_device_id,)
        )

        command = cur.fetchone()

        if not command:
            return {
                "success": True,
                "water": False,
                "message": "Não existem ordens de rega pendentes."
            }

        return {
            "success": True,
            "water": True,
            "command": {
                "id": command[0],
                "watering_device_id": command[1],
                "duration_seconds": command[2],
                "reason": command[3],
                "status": command[4],
                "created_at": command[5]
            }
        }

    finally:
        cur.close()
        conn.close()


# ============================================================

@app.post(
    "/watering-devices/code/{code}/command/{command_id}/complete"
)
def complete_watering_command(
    code: str,
    command_id: int
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar que o comando pertence ao módulo
        cur.execute(
            """
            SELECT
                wc.id,
                wc.status
            FROM watering_commands wc
            INNER JOIN watering_devices wd
                ON wc.watering_device_id = wd.id
            WHERE wc.id = %s
              AND wd.code = %s
            """,
            (
                command_id,
                code
            )
        )

        command = cur.fetchone()

        if not command:
            raise HTTPException(
                status_code=404,
                detail="Comando não encontrado."
            )

        if command[1] != "pending":
            raise HTTPException(
                status_code=400,
                detail="Este comando já foi processado."
            )

        # Marcar como executado
        cur.execute(
            """
            UPDATE watering_commands
            SET status = 'executed',
                executed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, status, executed_at
            """,
            (command_id,)
        )

        result = cur.fetchone()

        conn.commit()

        return {
            "success": True,
            "message": "Comando de rega executado com sucesso.",
            "command": {
                "id": result[0],
                "status": result[1],
                "executed_at": result[2]
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao completar comando: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


@app.post("/watering-devices/{watering_device_id}/command")
def create_watering_command(
    watering_device_id: int,
    request: ManualWateringCommandRequest
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar se o módulo de rega existe e está associado.
        cur.execute(
            """
            SELECT id, user_id, device_id
            FROM watering_devices
            WHERE id = %s
            """,
            (watering_device_id,)
        )

        modulo = cur.fetchone()

        if not modulo:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        if modulo[1] is None or modulo[2] is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "É necessário associar o módulo de rega "
                    "a um dispositivo."
                )
            )

        # Criar o comando pendente para o ESP32 consultar.
        cur.execute(
            """
            INSERT INTO watering_commands (
                watering_device_id,
                duration_seconds,
                reason,
                status,
                created_at
            )
            VALUES (%s, %s, %s, 'pending', CURRENT_TIMESTAMP)
            RETURNING id, watering_device_id, duration_seconds,
                      reason, status, created_at
            """,
            (
                watering_device_id,
                request.duration_seconds,
                request.reason
            )
        )

        comando = cur.fetchone()
        conn.commit()

        return {
            "success": True,
            "message": "Pedido de rega colocado na fila.",
            "command": {
                "id": comando[0],
                "watering_device_id": comando[1],
                "duration_seconds": comando[2],
                "reason": comando[3],
                "status": comando[4],
                "created_at": comando[5]
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as erro:
        conn.rollback()
        print("Erro ao criar comando de rega manual:", erro)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível criar o comando de rega manual."
        )

    finally:
        cur.close()
        conn.close()

# ============================================================
# HISTÓRICO DE REGA
# ============================================================

@app.get("/watering-devices/{watering_device_id}/history")
def get_watering_history(watering_device_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verificar módulo
        cur.execute(
            """
            SELECT id
            FROM watering_devices
            WHERE id = %s
            """,
            (watering_device_id,)
        )

        device = cur.fetchone()

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Módulo de rega não encontrado."
            )

        cur.execute(
            """
            SELECT
                id,
                watering_device_id,
                duration_seconds,
                reason,
                status,
                created_at,
                executed_at
            FROM watering_commands
            WHERE watering_device_id = %s
            ORDER BY created_at DESC
            """,
            (watering_device_id,)
        )

        rows = cur.fetchall()

        history = []

        for row in rows:
            history.append({
                "id": row[0],
                "watering_device_id": row[1],
                "duration_seconds": row[2],
                "reason": row[3],
                "status": row[4],
                "created_at": row[5],
                "executed_at": row[6]
            })

        return {
            "success": True,
            "history": history
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter histórico de rega: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()

#----------------------------------------------------------------------------
# PLANTAS
#----------------------------------------------------------------------------

# Obter todas as plantas disponíveis
@app.get("/plants")
def get_plants():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        name,
                        scientific_name,
                        min_soil_humidity,
                        max_soil_humidity,
                        min_air_temperature,
                        max_air_temperature,
                        min_night_temperature,
                        max_night_temperature,
                        min_air_humidity,
                        max_air_humidity,
                        drought_tolerance,
                        sunlight_requirement,
                        soil_type_preference,
                        watering_duration_seconds,
                        watering_cooldown_hours,
                        heat_stress_air_temperature,
                        heat_stress_watering_duration_seconds,
                        care_notes
                    FROM plants
                    ORDER BY name
                    """
                )

                plants = cur.fetchall()
                columns = [desc.name for desc in cur.description]


        resultado = []

        for plant in plants:

            resultado.append(dict(zip(columns, plant)))


        return {
            "success": True,
            "plants": resultado
        }

    except Exception as erro:

        print("Erro ao obter plantas:", erro)

        return {
            "success": False,
            "message": "Erro ao obter plantas."
        }


#----------------------------------------------------------------------------
# OBTER UMA PLANTA ESPECÍFICA
#----------------------------------------------------------------------------

@app.get("/plants/{plant_id}")
def get_plant(plant_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        name,
                        scientific_name,
                        min_soil_humidity,
                        max_soil_humidity,
                        min_night_temperature,
                        max_night_temperature,
                        min_air_temperature,
                        max_air_temperature,
                        min_air_humidity,
                        max_air_humidity,
                        drought_tolerance,
                        sunlight_requirement,
                        soil_type_preference,
                        watering_duration_seconds,
                        watering_cooldown_hours,
                        heat_stress_air_temperature,
                        heat_stress_watering_duration_seconds,
                        care_notes
                    FROM plants
                    WHERE id = %s
                    """,
                    (plant_id,)
                )

                plant = cur.fetchone()
                columns = [desc.name for desc in cur.description]


        if not plant:

            return {
                "success": False,
                "message": "Planta não encontrada."
            }


        return {
            "success": True,
            "plant": dict(zip(columns, plant))
        }

    except Exception as erro:

        print("Erro ao obter planta:", erro)

        return {
            "success": False,
            "message": "Erro ao obter planta."
        }


#----------------------------------------------------------------------------
# IPMA - ATUALIZAR DADOS
#----------------------------------------------------------------------------

@app.post("/ipma/update")
def update_ipma():

    try:

        total = atualizar_previsoes_ipma()

        return {
            "success": True,
            "message": "Dados do IPMA atualizados com sucesso.",
            "records": total
        }

    except Exception as erro:

        print("Erro ao atualizar IPMA:", erro)

        raise HTTPException(
            status_code=503,
            detail="Não foi possível atualizar os dados do IPMA neste momento."
        )


#----------------------------------------------------------------------------
# IPMA - CONSULTAR DADOS
#----------------------------------------------------------------------------

@app.get("/ipma")
def get_ipma():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT *
                    FROM ipma
                    ORDER BY id
                    """
                )

                data = cur.fetchall()

                # Obter nomes das colunas
                columns = [desc.name for desc in cur.description]


        resultado = []

        for row in data:

            resultado.append(
                dict(zip(columns, row))
            )


        return {
            "success": True,
            "data": resultado
        }

    except Exception as erro:

        print("Erro ao obter dados do IPMA:", erro)

        return {
            "success": False,
            "message": "Erro ao obter dados do IPMA."
        }