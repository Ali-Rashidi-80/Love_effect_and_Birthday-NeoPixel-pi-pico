import moderngl
import moderngl_window as mglw
import numpy as np
import math

class Heart3DArt(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "هنر قلب سه‌بعدی ولنتاین - جلوه هنری بالا"
    window_size = (800, 600)
    resource_dir = '.'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0.0
        
        # تولید نقاط قلب دوبعدی (با معادلات پارامتریک)
        self.heart2d = self.generate_heart_points(num_points=200, scale=0.05)
        # اکسترود کردن منحنی به مدل سه‌بعدی همراه با محاسبه نرمال‌ها
        vertices, indices = self.extrude_polygon(self.heart2d, thickness=0.2)
        self.heart_vbo = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.heart_ibo = self.ctx.buffer(indices.astype('i4').tobytes())
        
        # شیدرهای مدل قلب با افکت‌های انحراف و نورپردازی پیشرفته
        self.heart_prog = self.ctx.program(
            vertex_shader='''
            #version 330
            in vec3 in_position;
            in vec3 in_normal;
            uniform mat4 mvp;
            uniform mat4 model;
            uniform float time;
            out vec3 v_normal;
            out vec3 v_position;
            void main(){
                // انحراف دینامیک با دو تابع سینوسی و کسینوسی برای ایجاد حرکت‌های غیر یکنواخت
                vec3 displaced = in_position 
                    + in_normal * 0.01 * sin(time * 5.0 + in_position.x * 10.0)
                    + in_normal * 0.005 * cos(time * 7.0 + in_position.y * 15.0);
                vec4 pos = model * vec4(displaced, 1.0);
                v_position = pos.xyz;
                v_normal = normalize(mat3(model) * in_normal);
                gl_Position = mvp * vec4(displaced, 1.0);
            }
            ''',
            fragment_shader='''
            #version 330
            uniform float time;
            uniform vec3 light_dir;
            in vec3 v_normal;
            in vec3 v_position;
            out vec4 fragColor;
            void main(){
                vec3 norm = normalize(v_normal);
                vec3 light = normalize(light_dir);
                float diff = max(dot(norm, light), 0.0);
                vec3 view_dir = normalize(-v_position);
                vec3 reflect_dir = reflect(-light, norm);
                float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32.0);
                // تغییر رنگ دینامیک: از سرخ عمیق به صورتی با گذر زمان
                vec3 base_color = mix(vec3(0.8, 0.1, 0.1), vec3(1.0, 0.5, 0.6), 0.5 + 0.5*sin(time));
                // افزایش نمای افکت Fresnel برای درخشش لبه‌ها
                float fresnel = pow(1.0 - max(dot(norm, view_dir), 0.0), 3.0);
                // افزودن یک درخشش نرم (glow) به رنگ نهایی
                vec3 color = base_color * (0.3 + diff) + vec3(spec) + fresnel * vec3(0.25);
                fragColor = vec4(color, 1.0);
            }
            '''
        )
        self.heart_prog['light_dir'].value = (0.5, 1.0, 0.3)
        self.heart_vao = self.ctx.vertex_array(
            self.heart_prog,
            [(self.heart_vbo, '3f 3f', 'in_position', 'in_normal')],
            self.heart_ibo
        )
        
        # ایجاد فریم‌بافر آفلاین برای پست پردازش
        self.offscreen_texture = self.ctx.texture(self.wnd.size, components=4)
        self.offscreen_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.offscreen_fbo = self.ctx.framebuffer(color_attachments=[self.offscreen_texture])
        
        # کواد تمام صفحه برای پست پردازش
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
        ], dtype=np.float32)
        quad_indices = np.array([0,1,2, 0,2,3], dtype=np.int32)
        self.quad_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.quad_ibo = self.ctx.buffer(quad_indices.tobytes())
        
        self.post_prog = self.ctx.program(
            vertex_shader='''
            #version 330
            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 v_uv;
            void main(){
                v_uv = in_uv;
                gl_Position = vec4(in_pos, 0.0, 1.0);
            }
            ''',
            fragment_shader='''
            #version 330
            uniform sampler2D tex;
            uniform float time;
            in vec2 v_uv;
            out vec4 fragColor;
            
            void main(){
                // اعمال افکت وینیت
                vec2 uv = v_uv;
                // اعمال تغییر مختصات به صورت چرخشی (swirl) برای حس هنری
                vec2 centered = uv - vec2(0.5);
                float r = length(centered);
                float theta = atan(centered.y, centered.x);
                theta += 0.05 * sin(time + r * 10.0);
                uv = vec2(r * cos(theta), r * sin(theta)) + vec2(0.5);
                
                float vignette = smoothstep(0.8, 0.3, length(uv - vec2(0.5)));
                vec4 color = texture(tex, uv);
                // افزودن تغییر رنگ ملایم بر اساس زمان برای حس پویا
                color.rgb = mix(color.rgb, vec3(1.0, 0.85, 0.8), 0.1 * sin(time * 2.0));
                fragColor = vec4(color.rgb * vignette, color.a);
            }
            '''
        )
        self.quad_vao = self.ctx.vertex_array(
            self.post_prog,
            [(self.quad_vbo, '2f 2f', 'in_pos', 'in_uv')],
            self.quad_ibo
        )
    
    def generate_heart_points(self, num_points=200, scale=1.0):
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = 16 * (math.sin(angle) ** 3)
            y = 13 * math.cos(angle) - 5 * math.cos(2 * angle) - 2 * math.cos(3 * angle) - math.cos(4 * angle)
            points.append((x * scale, y * scale))
        return np.array(points, dtype=np.float32)
    
    def extrude_polygon(self, polygon, thickness=0.2):
        num_points = len(polygon)
        vertices = []
        indices = []
        front_z = thickness / 2
        back_z = -thickness / 2
        
        # وجه جلو
        front_vertices = []
        for (x, y) in polygon:
            front_vertices.append([x, y, front_z, 0.0, 0.0, 1.0])
        front_start = 0
        front_indices = []
        for i in range(1, num_points - 1):
            front_indices.extend([front_start, front_start + i, front_start + i + 1])
        
        # وجه عقب
        back_vertices = []
        for (x, y) in polygon:
            back_vertices.append([x, y, back_z, 0.0, 0.0, -1.0])
        back_start = len(front_vertices)
        back_indices = []
        for i in range(1, num_points - 1):
            back_indices.extend([back_start, back_start + i + 1, back_start + i])
        
        # وجوه جانبی
        side_vertices = []
        side_indices = []
        for i in range(num_points):
            next_i = (i + 1) % num_points
            p0 = polygon[i]
            p1 = polygon[next_i]
            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0:
                n = (0.0, 0.0, 0.0)
            else:
                n = (dy/length, -dx/length, 0.0)
            v0 = [p0[0], p0[1], front_z, n[0], n[1], n[2]]
            v1 = [p1[0], p1[1], front_z, n[0], n[1], n[2]]
            v2 = [p1[0], p1[1], back_z, n[0], n[1], n[2]]
            v3 = [p0[0], p0[1], back_z, n[0], n[1], n[2]]
            side_vertices.extend([v0, v1, v2, v3])
            base = i * 4
            side_indices.extend([base, base+1, base+2, base, base+2, base+3])
        side_start = len(front_vertices) + len(back_vertices)
        side_indices = (np.array(side_indices) + side_start).tolist()
        
        all_vertices = front_vertices + back_vertices + side_vertices
        all_indices = front_indices + back_indices + side_indices
        
        return np.array(all_vertices, dtype=np.float32), np.array(all_indices, dtype=np.int32)
    
    def scale_matrix(self, s):
        return np.array([
            [s, 0, 0, 0],
            [0, s, 0, 0],
            [0, 0, s, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
    
    def rotate(self, angle, axis):
        axis = np.array(axis, dtype=np.float32)
        axis = axis / np.linalg.norm(axis)
        a = math.radians(angle)
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        x, y, z = axis
        R = np.array([
            [cos_a + x*x*(1-cos_a),    x*y*(1-cos_a) - z*sin_a, x*z*(1-cos_a) + y*sin_a, 0],
            [y*x*(1-cos_a) + z*sin_a,  cos_a + y*y*(1-cos_a),    y*z*(1-cos_a) - x*sin_a, 0],
            [z*x*(1-cos_a) - y*sin_a,  z*y*(1-cos_a) + x*sin_a, cos_a + z*z*(1-cos_a),   0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        return R
    
    def perspective(self, fovy, aspect, near, far):
        f = 1.0 / math.tan(math.radians(fovy) / 2)
        M = np.zeros((4, 4), dtype=np.float32)
        M[0, 0] = f / aspect
        M[1, 1] = f
        M[2, 2] = (far + near) / (near - far)
        M[2, 3] = (2 * far * near) / (near - far)
        M[3, 2] = -1
        return M
    
    def look_at(self, eye, target, up):
        eye = np.array(eye, dtype=np.float32)
        target = np.array(target, dtype=np.float32)
        up = np.array(up, dtype=np.float32)
        f = target - eye
        f = f / np.linalg.norm(f)
        u = up / np.linalg.norm(up)
        s = np.cross(f, u)
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        M = np.eye(4, dtype=np.float32)
        M[0, :3] = s
        M[1, :3] = u
        M[2, :3] = -f
        M[0, 3] = -np.dot(s, eye)
        M[1, 3] = -np.dot(u, eye)
        M[2, 3] = np.dot(f, eye)
        return M
    
    def on_render(self, time, frame_time):
        # مرحله اول: رندر مدل قلب در فریم‌بافر آفلاین
        self.offscreen_fbo.use()
        self.ctx.clear(0.05, 0.05, 0.1)
        self.ctx.enable(moderngl.DEPTH_TEST)
        
        aspect_ratio = self.wnd.size[0] / self.wnd.size[1]
        projection = self.perspective(45.0, aspect_ratio, 0.1, 100.0)
        view = self.look_at(eye=(0.0, 0.0, 4.0), target=(0.0, 0.0, 0.0), up=(0.0, 1.0, 0.0))
        scale = 1.0 + 0.1 * math.sin(time * 3.0)
        model = self.rotate(self.angle, (0.0, 1.0, 0.0)) @ self.scale_matrix(scale)
        mvp = projection @ view @ model
        
        self.heart_prog['mvp'].write(mvp.astype('f4').tobytes())
        self.heart_prog['model'].write(model.astype('f4').tobytes())
        self.heart_prog['time'].value = time
        self.heart_vao.render()
        self.angle += frame_time * 30
        
        # مرحله دوم: پست پردازش روی تصویر رندر شده (اعمال افکت‌های هنری)
        self.ctx.screen.use()
        self.ctx.clear(0.0, 0.0, 0.0)
        self.post_prog['time'].value = time
        self.offscreen_texture.use(location=0)
        self.post_prog['tex'].value = 0
        self.quad_vao.render()

if __name__ == '__main__':
    mglw.run_window_config(Heart3DArt)
