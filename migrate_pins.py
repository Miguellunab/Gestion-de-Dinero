from app import app, db
from models import Profile
from passlib.hash import pbkdf2_sha256

with app.app_context():
    profiles = Profile.query.all()
    migrated_count = 0
    
    for profile in profiles:
        # Solo convertir PINs sin hashear (longitud 4)
        if len(profile.pin) == 4:
            old_pin = profile.pin
            profile.pin = pbkdf2_sha256.hash(old_pin)
            migrated_count += 1
    
    if migrated_count > 0:
        db.session.commit()
        print(f"Se migraron {migrated_count} perfiles correctamente")
    else:
        print("No se encontraron perfiles que necesiten migración")