from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, datetime, math

app = FastAPI(title="HRM VINACONEX - Full System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB = "hrm_full.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_nv TEXT UNIQUE NOT NULL, ho_ten TEXT NOT NULL,
        ngay_sinh TEXT, gioi_tinh TEXT, cccd TEXT,
        dien_thoai TEXT, email TEXT, dia_chi TEXT,
        don_vi TEXT, chuc_vu TEXT, ngay_vao TEXT,
        loai_hop_dong TEXT, luong_co_ban REAL DEFAULT 0,
        trang_thai TEXT DEFAULT 'Đang làm việc',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER, ma_hd TEXT UNIQUE,
        loai_hd TEXT, ngay_ky TEXT, ngay_bat_dau TEXT,
        ngay_ket_thuc TEXT, luong TEXT, ghi_chu TEXT,
        trang_thai TEXT DEFAULT 'Hiệu lực',
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER, thang INTEGER, nam INTEGER,
        ngay_cong REAL DEFAULT 0, ngay_phep REAL DEFAULT 0,
        ngay_le REAL DEFAULT 0, ngay_om REAL DEFAULT 0,
        ngay_vang TEXT DEFAULT '0', ghi_chu TEXT,
        UNIQUE(employee_id, thang, nam),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER, thang INTEGER, nam INTEGER,
        luong_co_ban REAL DEFAULT 0, he_so_luong REAL DEFAULT 1,
        phu_cap_chuc_vu REAL DEFAULT 0, phu_cap_di_lai REAL DEFAULT 0,
        phu_cap_an_trua REAL DEFAULT 0, thuong REAL DEFAULT 0,
        khau_tru REAL DEFAULT 0,
        bhxh_nv REAL DEFAULT 0, bhyt_nv REAL DEFAULT 0, bhtn_nv REAL DEFAULT 0,
        thue_tncn REAL DEFAULT 0, thuc_linh REAL DEFAULT 0,
        trang_thai TEXT DEFAULT 'Chờ duyệt',
        UNIQUE(employee_id, thang, nam),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS recruitment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vi_tri TEXT, don_vi TEXT, so_luong INTEGER DEFAULT 1,
        mo_ta TEXT, yeu_cau TEXT, ngay_dang TEXT,
        han_nop TEXT, trang_thai TEXT DEFAULT 'Đang tuyển',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recruitment_id INTEGER, ho_ten TEXT, email TEXT,
        dien_thoai TEXT, trinh_do TEXT, kinh_nghiem TEXT,
        ngay_nop TEXT, trang_thai TEXT DEFAULT 'Mới nộp',
        ghi_chu TEXT,
        FOREIGN KEY(recruitment_id) REFERENCES recruitment(id)
    );
    CREATE TABLE IF NOT EXISTS training (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ten_khoa TEXT, don_vi_to_chuc TEXT, noi_dung TEXT,
        ngay_bat_dau TEXT, ngay_ket_thuc TEXT, dia_diem TEXT,
        chi_phi REAL DEFAULT 0, trang_thai TEXT DEFAULT 'Kế hoạch',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS training_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        training_id INTEGER, employee_id INTEGER,
        ket_qua TEXT, chung_chi TEXT, ghi_chu TEXT,
        FOREIGN KEY(training_id) REFERENCES training(id),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER, loai TEXT, ten_hinh_thuc TEXT,
        ly_do TEXT, ngay_quyet_dinh TEXT, so_quyet_dinh TEXT,
        gia_tri REAL DEFAULT 0, ghi_chu TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    CREATE TABLE IF NOT EXISTS insurance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER UNIQUE,
        so_so_bhxh TEXT, so_the_bhyt TEXT,
        ngay_tham_gia TEXT, muc_dong REAL DEFAULT 0,
        noi_kham TEXT, trang_thai TEXT DEFAULT 'Đang đóng',
        ghi_chu TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    """)
    # Seed employees
    seed_emp = [
        ("VNX-001","Nguyễn Văn An","1985-03-12","Nam","001085012345","0912345678","an.nv@vinaconex.com.vn","Hà Nội","Ban Tổ chức - Nhân sự","Trưởng ban","2010-06-01","Hợp đồng không xác định thời hạn",15000000,"Đang làm việc"),
        ("VNX-002","Trần Thị Bình","1990-07-25","Nữ","001090067891","0987654321","binh.tt@vinaconex.com.vn","Hà Nội","Ban Tài chính - Kế toán","Chuyên viên","2015-01-10","Hợp đồng không xác định thời hạn",12000000,"Đang làm việc"),
        ("VNX-003","Lê Minh Cường","1988-11-05","Nam","001088034567","0965432100","cuong.lm@vinaconex.com.vn","Hà Nội","Ban Kỹ thuật","Phó trưởng ban","2012-03-15","Hợp đồng không xác định thời hạn",18000000,"Đang làm việc"),
        ("VNX-004","Phạm Thu Hà","1995-02-18","Nữ","001095078902","0934567890","ha.pt@vinaconex.com.vn","Hà Nội","Công đoàn","Chuyên viên","2020-08-01","Hợp đồng xác định thời hạn",10000000,"Đang làm việc"),
        ("VNX-005","Hoàng Đức Mạnh","1982-09-30","Nam","001082056123","0901234567","manh.hd@vinaconex.com.vn","Hà Nội","Ban Phát triển Nhân lực","Trưởng ban","2008-01-20","Hợp đồng không xác định thời hạn",20000000,"Đang làm việc"),
        ("VNX-006","Vũ Thị Lan","1993-05-14","Nữ","001093045678","0978123456","lan.vt@vinaconex.com.vn","Hà Nội","Ban Pháp chế","Chuyên viên","2018-04-01","Hợp đồng không xác định thời hạn",11000000,"Đang làm việc"),
        ("VNX-007","Đặng Văn Hùng","1979-12-20","Nam","001079023456","0911222333","hung.dv@vinaconex.com.vn","Hà Nội","Văn phòng Tổng công ty","Chánh văn phòng","2005-07-10","Hợp đồng không xác định thời hạn",22000000,"Đang làm việc"),
    ]
    for s in seed_emp:
        try: c.execute("INSERT INTO employees (ma_nv,ho_ten,ngay_sinh,gioi_tinh,cccd,dien_thoai,email,dia_chi,don_vi,chuc_vu,ngay_vao,loai_hop_dong,luong_co_ban,trang_thai) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", s)
        except: pass
    # Seed contracts
    seed_hd = [
        (1,"HD-2024-001","Hợp đồng không xác định thời hạn","2024-01-01","2024-01-01",None,"15,000,000",""),
        (2,"HD-2024-002","Hợp đồng xác định thời hạn","2024-01-10","2024-01-10","2026-01-09","12,000,000",""),
        (3,"HD-2024-003","Hợp đồng không xác định thời hạn","2024-03-15","2024-03-15",None,"18,000,000",""),
        (4,"HD-2026-004","Hợp đồng xác định thời hạn","2026-01-01","2026-01-01","2026-09-30","10,000,000","Sắp hết hạn"),
        (5,"HD-2024-005","Hợp đồng không xác định thời hạn","2024-01-20","2024-01-20",None,"20,000,000",""),
    ]
    for s in seed_hd:
        try: c.execute("INSERT INTO contracts (employee_id,ma_hd,loai_hd,ngay_ky,ngay_bat_dau,ngay_ket_thuc,luong,ghi_chu) VALUES (?,?,?,?,?,?,?,?)", s)
        except: pass
    # Seed attendance
    for eid in range(1,8):
        try: c.execute("INSERT INTO attendance (employee_id,thang,nam,ngay_cong,ngay_phep,ngay_le,ngay_om) VALUES (?,6,2026,22,1,0,0)", (eid,))
        except: pass
    # Seed payroll
    for i,eid in enumerate(range(1,8)):
        luong = [15,12,18,10,20,11,22][i]*1000000
        bhxh = luong*0.08; bhyt = luong*0.015; bhtn = luong*0.01
        thuc = luong - bhxh - bhyt - bhtn
        try: c.execute("INSERT INTO payroll (employee_id,thang,nam,luong_co_ban,phu_cap_chuc_vu,phu_cap_di_lai,phu_cap_an_trua,bhxh_nv,bhyt_nv,bhtn_nv,thuc_linh,trang_thai) VALUES (?,6,2026,?,500000,300000,730000,?,?,?,?,'Chờ duyệt')", (eid,luong,bhxh,bhyt,bhtn,thuc+1530000))
        except: pass
    # Seed recruitment
    seed_rec = [
        ("Chuyên viên nhân sự","Ban Tổ chức - Nhân sự",2,"Tuyển chuyên viên nhân sự","Tốt nghiệp ĐH chuyên ngành Quản trị nhân lực","2026-05-01","2026-07-31","Đang tuyển"),
        ("Kế toán viên","Ban Tài chính - Kế toán",1,"Tuyển kế toán viên","Tốt nghiệp ĐH Kế toán, có chứng chỉ CPA","2026-06-01","2026-08-31","Đang tuyển"),
        ("Kỹ sư xây dựng","Ban Kỹ thuật",3,"Tuyển kỹ sư xây dựng","Tốt nghiệp ĐH Xây dựng, kinh nghiệm 2 năm","2026-04-01","2026-06-30","Đã đóng"),
    ]
    for s in seed_rec:
        try: c.execute("INSERT INTO recruitment (vi_tri,don_vi,so_luong,mo_ta,yeu_cau,ngay_dang,han_nop,trang_thai) VALUES (?,?,?,?,?,?,?,?)", s)
        except: pass
    # Seed training
    seed_tr = [
        ("Kỹ năng soạn thảo văn bản hành chính","Ban Tổ chức - Nhân sự","Soạn thảo công văn, quyết định, tờ trình","2026-07-10","2026-07-12","Hội trường VINACONEX",0,"Kế hoạch"),
        ("Bồi dưỡng Đảng viên","Đảng ủy VINACONEX","Nghiệp vụ công tác Đảng","2026-08-01","2026-08-03","Trụ sở Tổng công ty",0,"Kế hoạch"),
        ("An toàn lao động","Ban Kỹ thuật","Huấn luyện ATLĐ định kỳ","2026-06-15","2026-06-16","Hội trường A",500000,"Hoàn thành"),
    ]
    for s in seed_tr:
        try: c.execute("INSERT INTO training (ten_khoa,don_vi_to_chuc,noi_dung,ngay_bat_dau,ngay_ket_thuc,dia_diem,chi_phi,trang_thai) VALUES (?,?,?,?,?,?,?,?)", s)
        except: pass
    # Seed rewards
    seed_rw = [
        (5,"Khen thưởng","Bằng khen Tổng Giám đốc","Hoàn thành xuất sắc nhiệm vụ năm 2025","2026-01-15","QĐ-25/2026",5000000,""),
        (3,"Khen thưởng","Chiến sĩ thi đua","Đạt danh hiệu CSTĐ cơ sở năm 2025","2026-01-15","QĐ-26/2026",3000000,""),
        (4,"Kỷ luật","Khiển trách","Đi muộn nhiều lần","2026-03-01","QĐ-12/2026",0,"Lần đầu"),
    ]
    for s in seed_rw:
        try: c.execute("INSERT INTO rewards (employee_id,loai,ten_hinh_thuc,ly_do,ngay_quyet_dinh,so_quyet_dinh,gia_tri,ghi_chu) VALUES (?,?,?,?,?,?,?,?)", s)
        except: pass
    # Seed insurance
    for i,eid in enumerate(range(1,8)):
        try: c.execute("INSERT INTO insurance (employee_id,so_so_bhxh,so_the_bhyt,ngay_tham_gia,muc_dong,noi_kham,trang_thai) VALUES (?,?,?,?,?,?,'Đang đóng')", (eid,f"0100{1000+eid}",f"DN{4000+eid:06}","2024-01-01",[15,12,18,10,20,11,22][i]*1000000*0.105,"BV Bạch Mai"))
        except: pass
    c.commit(); c.close()

init()

# ─── MODELS ───
class EmployeeModel(BaseModel):
    ma_nv: str; ho_ten: str; ngay_sinh: Optional[str]=None; gioi_tinh: Optional[str]=None
    cccd: Optional[str]=None; dien_thoai: Optional[str]=None; email: Optional[str]=None
    dia_chi: Optional[str]=None; don_vi: Optional[str]=None; chuc_vu: Optional[str]=None
    ngay_vao: Optional[str]=None; loai_hop_dong: Optional[str]=None
    luong_co_ban: Optional[float]=0; trang_thai: Optional[str]="Đang làm việc"

class ContractModel(BaseModel):
    employee_id: int; ma_hd: str; loai_hd: str; ngay_ky: str
    ngay_bat_dau: str; ngay_ket_thuc: Optional[str]=None
    luong: Optional[str]=None; ghi_chu: Optional[str]=None; trang_thai: Optional[str]="Hiệu lực"

class AttendanceModel(BaseModel):
    employee_id: int; thang: int; nam: int
    ngay_cong: float=0; ngay_phep: float=0; ngay_le: float=0; ngay_om: float=0; ghi_chu: Optional[str]=None

class PayrollModel(BaseModel):
    employee_id: int; thang: int; nam: int
    luong_co_ban: float=0; he_so_luong: float=1
    phu_cap_chuc_vu: float=0; phu_cap_di_lai: float=0; phu_cap_an_trua: float=0
    thuong: float=0; khau_tru: float=0; trang_thai: Optional[str]="Chờ duyệt"

class RecruitmentModel(BaseModel):
    vi_tri: str; don_vi: str; so_luong: int=1; mo_ta: Optional[str]=None
    yeu_cau: Optional[str]=None; ngay_dang: Optional[str]=None
    han_nop: Optional[str]=None; trang_thai: Optional[str]="Đang tuyển"

class CandidateModel(BaseModel):
    recruitment_id: int; ho_ten: str; email: Optional[str]=None
    dien_thoai: Optional[str]=None; trinh_do: Optional[str]=None
    kinh_nghiem: Optional[str]=None; ngay_nop: Optional[str]=None
    trang_thai: Optional[str]="Mới nộp"; ghi_chu: Optional[str]=None

class TrainingModel(BaseModel):
    ten_khoa: str; don_vi_to_chuc: Optional[str]=None; noi_dung: Optional[str]=None
    ngay_bat_dau: Optional[str]=None; ngay_ket_thuc: Optional[str]=None
    dia_diem: Optional[str]=None; chi_phi: float=0; trang_thai: Optional[str]="Kế hoạch"

class RewardModel(BaseModel):
    employee_id: int; loai: str; ten_hinh_thuc: str; ly_do: Optional[str]=None
    ngay_quyet_dinh: Optional[str]=None; so_quyet_dinh: Optional[str]=None
    gia_tri: float=0; ghi_chu: Optional[str]=None

class InsuranceModel(BaseModel):
    employee_id: int; so_so_bhxh: Optional[str]=None; so_the_bhyt: Optional[str]=None
    ngay_tham_gia: Optional[str]=None; muc_dong: float=0
    noi_kham: Optional[str]=None; trang_thai: Optional[str]="Đang đóng"; ghi_chu: Optional[str]=None

# ─── STATS ───
@app.get("/stats")
def stats():
    c = db()
    total = c.execute("SELECT COUNT(*) FROM employees WHERE trang_thai='Đang làm việc'").fetchone()[0]
    by_unit = [dict(r) for r in c.execute("SELECT don_vi, COUNT(*) cnt FROM employees WHERE trang_thai='Đang làm việc' GROUP BY don_vi").fetchall()]
    avg_sal = c.execute("SELECT AVG(luong_co_ban) FROM employees WHERE trang_thai='Đang làm việc'").fetchone()[0] or 0
    exp_contracts = c.execute("SELECT COUNT(*) FROM contracts WHERE ngay_ket_thuc IS NOT NULL AND ngay_ket_thuc <= date('now','+90 days') AND trang_thai='Hiệu lực'").fetchone()[0]
    open_rec = c.execute("SELECT COUNT(*) FROM recruitment WHERE trang_thai='Đang tuyển'").fetchone()[0]
    payroll_pending = c.execute("SELECT COUNT(*) FROM payroll WHERE trang_thai='Chờ duyệt' AND thang=6 AND nam=2026").fetchone()[0]
    c.close()
    return {"total": total, "by_unit": by_unit, "avg_salary": round(avg_sal), "exp_contracts": exp_contracts, "open_recruitment": open_rec, "payroll_pending": payroll_pending}

# ─── EMPLOYEES ───
@app.get("/employees")
def list_emp(search: Optional[str]=None, don_vi: Optional[str]=None, trang_thai: Optional[str]=None):
    c = db(); q = "SELECT * FROM employees WHERE 1=1"; p = []
    if search: q += " AND (ho_ten LIKE ? OR ma_nv LIKE ? OR email LIKE ?)"; p += [f"%{search}%"]*3
    if don_vi: q += " AND don_vi=?"; p.append(don_vi)
    if trang_thai: q += " AND trang_thai=?"; p.append(trang_thai)
    r = [dict(x) for x in c.execute(q+" ORDER BY id", p).fetchall()]; c.close(); return r

@app.post("/employees", status_code=201)
def create_emp(e: EmployeeModel):
    c = db()
    try:
        cur = c.execute("INSERT INTO employees (ma_nv,ho_ten,ngay_sinh,gioi_tinh,cccd,dien_thoai,email,dia_chi,don_vi,chuc_vu,ngay_vao,loai_hop_dong,luong_co_ban,trang_thai) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(e.ma_nv,e.ho_ten,e.ngay_sinh,e.gioi_tinh,e.cccd,e.dien_thoai,e.email,e.dia_chi,e.don_vi,e.chuc_vu,e.ngay_vao,e.loai_hop_dong,e.luong_co_ban,e.trang_thai))
        c.commit(); nid=cur.lastrowid
    except sqlite3.IntegrityError: raise HTTPException(400,"Mã NV đã tồn tại")
    finally: c.close()
    return {"id":nid}

@app.put("/employees/{eid}")
def update_emp(eid:int, e: EmployeeModel):
    c = db(); c.execute("UPDATE employees SET ma_nv=?,ho_ten=?,ngay_sinh=?,gioi_tinh=?,cccd=?,dien_thoai=?,email=?,dia_chi=?,don_vi=?,chuc_vu=?,ngay_vao=?,loai_hop_dong=?,luong_co_ban=?,trang_thai=? WHERE id=?",(e.ma_nv,e.ho_ten,e.ngay_sinh,e.gioi_tinh,e.cccd,e.dien_thoai,e.email,e.dia_chi,e.don_vi,e.chuc_vu,e.ngay_vao,e.loai_hop_dong,e.luong_co_ban,e.trang_thai,eid)); c.commit(); c.close(); return {"ok":True}

@app.delete("/employees/{eid}")
def del_emp(eid:int):
    c=db(); c.execute("UPDATE employees SET trang_thai='Đã nghỉ việc' WHERE id=?", (eid,)); c.commit(); c.close(); return {"ok":True}

# ─── CONTRACTS ───
@app.get("/contracts")
def list_contracts(employee_id: Optional[int]=None, expiring: Optional[bool]=None):
    c=db(); q="SELECT ct.*,e.ho_ten,e.ma_nv,e.don_vi FROM contracts ct JOIN employees e ON ct.employee_id=e.id WHERE 1=1"; p=[]
    if employee_id: q+=" AND ct.employee_id=?"; p.append(employee_id)
    if expiring: q+=" AND ct.ngay_ket_thuc IS NOT NULL AND ct.ngay_ket_thuc<=date('now','+90 days') AND ct.trang_thai='Hiệu lực'"
    r=[dict(x) for x in c.execute(q+" ORDER BY ct.id DESC",p).fetchall()]; c.close(); return r

@app.post("/contracts", status_code=201)
def create_contract(ct: ContractModel):
    c=db()
    try: cur=c.execute("INSERT INTO contracts (employee_id,ma_hd,loai_hd,ngay_ky,ngay_bat_dau,ngay_ket_thuc,luong,ghi_chu,trang_thai) VALUES (?,?,?,?,?,?,?,?,?)",(ct.employee_id,ct.ma_hd,ct.loai_hd,ct.ngay_ky,ct.ngay_bat_dau,ct.ngay_ket_thuc,ct.luong,ct.ghi_chu,ct.trang_thai)); c.commit(); nid=cur.lastrowid
    except: raise HTTPException(400,"Lỗi tạo hợp đồng")
    finally: c.close()
    return {"id":nid}

# ─── ATTENDANCE ───
@app.get("/attendance")
def list_att(thang: int=6, nam: int=2026, don_vi: Optional[str]=None):
    c=db(); q="SELECT a.*,e.ho_ten,e.ma_nv,e.don_vi FROM attendance a JOIN employees e ON a.employee_id=e.id WHERE a.thang=? AND a.nam=?"; p=[thang,nam]
    if don_vi: q+=" AND e.don_vi=?"; p.append(don_vi)
    r=[dict(x) for x in c.execute(q,p).fetchall()]; c.close(); return r

@app.put("/attendance")
def upsert_att(a: AttendanceModel):
    c=db(); c.execute("INSERT INTO attendance (employee_id,thang,nam,ngay_cong,ngay_phep,ngay_le,ngay_om,ghi_chu) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(employee_id,thang,nam) DO UPDATE SET ngay_cong=?,ngay_phep=?,ngay_le=?,ngay_om=?,ghi_chu=?",(a.employee_id,a.thang,a.nam,a.ngay_cong,a.ngay_phep,a.ngay_le,a.ngay_om,a.ghi_chu,a.ngay_cong,a.ngay_phep,a.ngay_le,a.ngay_om,a.ghi_chu)); c.commit(); c.close(); return {"ok":True}

# ─── PAYROLL ───
@app.get("/payroll")
def list_payroll(thang: int=6, nam: int=2026, don_vi: Optional[str]=None):
    c=db(); q="SELECT p.*,e.ho_ten,e.ma_nv,e.don_vi FROM payroll p JOIN employees e ON p.employee_id=e.id WHERE p.thang=? AND p.nam=?"; p=[thang,nam]
    if don_vi: q+=" AND e.don_vi=?"; p.append(don_vi)
    r=[dict(x) for x in c.execute(q,p).fetchall()]; c.close(); return r

@app.post("/payroll/calculate")
def calc_payroll(thang: int=6, nam: int=2026):
    c=db()
    emps=c.execute("SELECT id,luong_co_ban FROM employees WHERE trang_thai='Đang làm việc'").fetchall()
    for e in emps:
        lb=e["luong_co_ban"]; bhxh=lb*0.08; bhyt=lb*0.015; bhtn=lb*0.01
        phu_cap=1530000; thuc=lb+phu_cap-bhxh-bhyt-bhtn
        try: c.execute("INSERT INTO payroll (employee_id,thang,nam,luong_co_ban,phu_cap_chuc_vu,phu_cap_di_lai,phu_cap_an_trua,bhxh_nv,bhyt_nv,bhtn_nv,thuc_linh) VALUES (?,?,?,?,500000,300000,730000,?,?,?,?) ON CONFLICT(employee_id,thang,nam) DO UPDATE SET luong_co_ban=?,bhxh_nv=?,bhyt_nv=?,bhtn_nv=?,thuc_linh=?",(e["id"],thang,nam,lb,bhxh,bhyt,bhtn,thuc,lb,bhxh,bhyt,bhtn,thuc))
        except: pass
    c.commit(); c.close(); return {"ok":True,"calculated":len(emps)}

@app.put("/payroll/{pid}/approve")
def approve_payroll(pid:int):
    c=db(); c.execute("UPDATE payroll SET trang_thai='Đã duyệt' WHERE id=?", (pid,)); c.commit(); c.close(); return {"ok":True}

# ─── RECRUITMENT ───
@app.get("/recruitment")
def list_rec(trang_thai: Optional[str]=None):
    c=db(); q="SELECT r.*,(SELECT COUNT(*) FROM candidates WHERE recruitment_id=r.id) so_ung_vien FROM recruitment r WHERE 1=1"; p=[]
    if trang_thai: q+=" AND r.trang_thai=?"; p.append(trang_thai)
    r=[dict(x) for x in c.execute(q+" ORDER BY r.id DESC",p).fetchall()]; c.close(); return r

@app.post("/recruitment", status_code=201)
def create_rec(r: RecruitmentModel):
    c=db(); cur=c.execute("INSERT INTO recruitment (vi_tri,don_vi,so_luong,mo_ta,yeu_cau,ngay_dang,han_nop,trang_thai) VALUES (?,?,?,?,?,?,?,?)",(r.vi_tri,r.don_vi,r.so_luong,r.mo_ta,r.yeu_cau,r.ngay_dang,r.han_nop,r.trang_thai)); c.commit(); nid=cur.lastrowid; c.close(); return {"id":nid}

@app.get("/candidates")
def list_cand(recruitment_id: Optional[int]=None):
    c=db(); q="SELECT * FROM candidates WHERE 1=1"; p=[]
    if recruitment_id: q+=" AND recruitment_id=?"; p.append(recruitment_id)
    r=[dict(x) for x in c.execute(q+" ORDER BY id DESC",p).fetchall()]; c.close(); return r

@app.post("/candidates", status_code=201)
def create_cand(cd: CandidateModel):
    c=db(); cur=c.execute("INSERT INTO candidates (recruitment_id,ho_ten,email,dien_thoai,trinh_do,kinh_nghiem,ngay_nop,trang_thai,ghi_chu) VALUES (?,?,?,?,?,?,?,?,?)",(cd.recruitment_id,cd.ho_ten,cd.email,cd.dien_thoai,cd.trinh_do,cd.kinh_nghiem,cd.ngay_nop,cd.trang_thai,cd.ghi_chu)); c.commit(); nid=cur.lastrowid; c.close(); return {"id":nid}

@app.put("/candidates/{cid}/status")
def update_cand(cid:int, trang_thai:str=Query(...)):
    c=db(); c.execute("UPDATE candidates SET trang_thai=? WHERE id=?",(trang_thai,cid)); c.commit(); c.close(); return {"ok":True}

# ─── TRAINING ───
@app.get("/training")
def list_training(trang_thai: Optional[str]=None):
    c=db(); q="SELECT t.*,(SELECT COUNT(*) FROM training_participants WHERE training_id=t.id) so_hv FROM training t WHERE 1=1"; p=[]
    if trang_thai: q+=" AND t.trang_thai=?"; p.append(trang_thai)
    r=[dict(x) for x in c.execute(q+" ORDER BY t.id DESC",p).fetchall()]; c.close(); return r

@app.post("/training", status_code=201)
def create_training(t: TrainingModel):
    c=db(); cur=c.execute("INSERT INTO training (ten_khoa,don_vi_to_chuc,noi_dung,ngay_bat_dau,ngay_ket_thuc,dia_diem,chi_phi,trang_thai) VALUES (?,?,?,?,?,?,?,?)",(t.ten_khoa,t.don_vi_to_chuc,t.noi_dung,t.ngay_bat_dau,t.ngay_ket_thuc,t.dia_diem,t.chi_phi,t.trang_thai)); c.commit(); nid=cur.lastrowid; c.close(); return {"id":nid}

# ─── REWARDS ───
@app.get("/rewards")
def list_rewards(loai: Optional[str]=None):
    c=db(); q="SELECT r.*,e.ho_ten,e.ma_nv,e.don_vi FROM rewards r JOIN employees e ON r.employee_id=e.id WHERE 1=1"; p=[]
    if loai: q+=" AND r.loai=?"; p.append(loai)
    r=[dict(x) for x in c.execute(q+" ORDER BY r.id DESC",p).fetchall()]; c.close(); return r

@app.post("/rewards", status_code=201)
def create_reward(r: RewardModel):
    c=db(); cur=c.execute("INSERT INTO rewards (employee_id,loai,ten_hinh_thuc,ly_do,ngay_quyet_dinh,so_quyet_dinh,gia_tri,ghi_chu) VALUES (?,?,?,?,?,?,?,?)",(r.employee_id,r.loai,r.ten_hinh_thuc,r.ly_do,r.ngay_quyet_dinh,r.so_quyet_dinh,r.gia_tri,r.ghi_chu)); c.commit(); nid=cur.lastrowid; c.close(); return {"id":nid}

# ─── INSURANCE ───
@app.get("/insurance")
def list_insurance(trang_thai: Optional[str]=None):
    c=db(); q="SELECT i.*,e.ho_ten,e.ma_nv,e.don_vi,e.luong_co_ban FROM insurance i JOIN employees e ON i.employee_id=e.id WHERE 1=1"; p=[]
    if trang_thai: q+=" AND i.trang_thai=?"; p.append(trang_thai)
    r=[dict(x) for x in c.execute(q+" ORDER BY i.id",p).fetchall()]; c.close(); return r

@app.post("/insurance", status_code=201)
def create_insurance(ins: InsuranceModel):
    c=db()
    try: cur=c.execute("INSERT INTO insurance (employee_id,so_so_bhxh,so_the_bhyt,ngay_tham_gia,muc_dong,noi_kham,trang_thai,ghi_chu) VALUES (?,?,?,?,?,?,?,?)",(ins.employee_id,ins.so_so_bhxh,ins.so_the_bhyt,ins.ngay_tham_gia,ins.muc_dong,ins.noi_kham,ins.trang_thai,ins.ghi_chu)); c.commit(); nid=cur.lastrowid
    except: raise HTTPException(400,"Đã có hồ sơ bảo hiểm")
    finally: c.close()
    return {"id":nid}

import sqlite3
