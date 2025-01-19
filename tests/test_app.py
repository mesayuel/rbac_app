# tests/test_app.py

import unittest
import json
from app import app, db
from models import User, Role, Permission

class RBACAppTestCase(unittest.TestCase):
    def setUp(self):
        # Konfigurasi aplikasi untuk testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_user(self):
        response = self.client.post('/users', json={'username': 'Alice'})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('User Alice created', data['message'])
        self.assertEqual(data['user_id'], 1)

    def test_add_user_without_username(self):
        response = self.client.post('/users', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Username is required', data['message'])

    def test_add_duplicate_user(self):
        self.client.post('/users', json={'username': 'Alice'})
        response = self.client.post('/users', json={'username': 'Alice'})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('User already exists', data['message'])

    def test_get_user(self):
        # Tambah user terlebih dahulu
        self.client.post('/users', json={'username': 'Alice'})
        response = self.client.get('/users/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['username'], 'Alice')
        self.assertEqual(data['roles'], [])

    def test_add_role(self):
        response = self.client.post('/roles', json={'name': 'Editor'})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('Role Editor created', data['message'])
        self.assertEqual(data['role_id'], 1)

    def test_add_permission(self):
        response = self.client.post('/permissions', json={'name': 'edit_document'})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('Permission edit_document created', data['message'])
        self.assertEqual(data['permission_id'], 1)

    def test_assign_role_to_user(self):
        # Tambah user dan role terlebih dahulu
        self.client.post('/users', json={'username': 'Alice'})
        self.client.post('/roles', json={'name': 'Editor'})
        response = self.client.post('/users/1/roles', json={'role_id': 1})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Role Editor assigned to user Alice', data['message'])

    def test_assign_permission_to_role(self):
        # Tambah role dan permission terlebih dahulu
        self.client.post('/roles', json={'name': 'Editor'})
        self.client.post('/permissions', json={'name': 'edit_document'})
        response = self.client.post('/roles/1/permissions', json={'permission_id': 1})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Permission edit_document assigned to role Editor', data['message'])

    def test_check_access(self):
        # Setup: Tambah user, role, permission, assign role ke user, assign permission ke role
        self.client.post('/users', json={'username': 'Alice'})
        self.client.post('/roles', json={'name': 'Editor'})
        self.client.post('/permissions', json={'name': 'edit_document'})
        self.client.post('/users/1/roles', json={'role_id': 1})
        self.client.post('/roles/1/permissions', json={'permission_id': 1})

        # Cek akses
        response = self.client.post('/check_access', json={
            'username': 'Alice',
            'input_text': 'Can I edit this document?'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['has_access'])
        self.assertEqual(data['intent'], 'edit_document')

    def test_check_access_without_user(self):
        response = self.client.post('/check_access', json={
            'username': 'Bob',
            'input_text': 'Can I edit this document?'
        })
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('User not found', data['message'])

    def test_check_access_without_permission(self):
        # Setup: Tambah user dan role tetapi tidak ada permission
        self.client.post('/users', json={'username': 'Alice'})
        self.client.post('/roles', json={'name': 'Editor'})
        self.client.post('/users/1/roles', json={'role_id': 1})

        # Cek akses
        response = self.client.post('/check_access', json={
            'username': 'Alice',
            'input_text': 'Can I edit this document?'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['has_access'])
        self.assertEqual(data['intent'], 'edit_document')

    def test_add_permission_without_name(self):
        response = self.client.post('/permissions', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Permission name is required', data['message'])

    def test_add_role_without_name(self):
        response = self.client.post('/roles', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Role name is required', data['message'])

if __name__ == '__main__':
    unittest.main()