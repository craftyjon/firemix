# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

from builtins import str
from builtins import range
from PyQt5 import QtCore, QtGui, QtWidgets

from ui.ui_dlg_settings import Ui_DlgSettings
from lib import color_modes

# TODO: This is a hack
PROTOCOLS = ["Legacy", "OPC"]


class DlgSettings(QtWidgets.QDialog, Ui_DlgSettings):

    def __init__(self, parent=None):
        super(DlgSettings, self).__init__(parent)
        self.playlist = parent.app.playlist
        self.setupUi(self)
        self.app = parent.app

        # Setup tree view
        self.tree_settings.itemClicked.connect(self.on_tree_changed)
        self.settings_stack.setCurrentIndex(0)

        # Setup events for all panes
        self.btn_networking_add_client.clicked.connect(self.add_networking_client_row)
        self.btn_networking_del_client.clicked.connect(self.del_networking_client_row)
        self.tbl_networking_clients.itemChanged.connect(self.validate_networking_client_table_item)

        self.port_validator = QtGui.QIntValidator(1, 65535, self)
        ip_regex = QtCore.QRegExp(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        host_regex = QtCore.QRegExp(r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
        self.ip_validator = QtGui.QRegExpValidator(ip_regex, self)
        self.host_validator = QtGui.QRegExpValidator(host_regex, self)

        # Setup validation and acceptance methods for all panes
        self.validators = [self.validate_networking, self.validate_mixer]
        self.acceptors = [self.accept_networking, self.accept_strands, self.accept_mixer, self.save_settings]

        # Initialize settings panes
        self.populate_mixer_settings()
        self.populate_networking_clients_table()
        self.populate_strand_settings_table()

    def on_tree_changed(self):
        self.settings_stack.setCurrentIndex(self.tree_settings.currentIndex().row())

    def validate(self):
        valid = True
        for validator in self.validators:
            if not validator():
                valid = False
        return valid

    def validate_networking(self):
        for row in range(self.tbl_networking_clients.rowCount()):
            for col in range(self.tbl_networking_clients.columnCount()):
                if not self.validate_networking_client_table_item(self.tbl_networking_clients.item(row, col)):
                    return False
        return True

    def validate_networking_client_table_item(self, item):
        if item is None:
            return True
        valid = None
        if item.column() == 0:  # host address
            valid, _, _ = self.host_validator.validate(item.text(), 0)
            if valid != QtGui.QValidator.Acceptable:
                valid, _, _ = self.ip_validator.validate(item.text(), 0)
        elif item.column() == 1:  # Port
            valid, _, _ = self.port_validator.validate(item.text(), 0)
        else:
            return True

        if valid == QtGui.QValidator.Invalid:
            item.setBackground(QtGui.QColor(255, 190, 190))
        elif valid == QtGui.QValidator.Intermediate:
            item.setBackground(QtGui.QColor(255, 255, 190))
        else:
            item.setBackground(QtGui.QColor(0, 0, 0, 0))

        return (valid == QtGui.QValidator.Acceptable)

    def accept(self):
        if self.validate():
            for acceptor in self.acceptors:
                acceptor()

            QtWidgets.QDialog.accept(self)
        else:
            QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "FireMix", "Please correct all highlighted entries!").exec_()

    def accept_networking(self):
        clients = []
        for i in range(self.tbl_networking_clients.rowCount()):
            host = self.tbl_networking_clients.item(i, 0).text()
            port = int(self.tbl_networking_clients.item(i, 1).text())
            enabled = (self.tbl_networking_clients.cellWidget(i, 2).checkState() == QtCore.Qt.Checked)
            color_mode = self.tbl_networking_clients.cellWidget(i, 3).currentText()
            proto = self.tbl_networking_clients.cellWidget(i, 4).currentText()
            ignore_dimming = (self.tbl_networking_clients.cellWidget(i, 5).checkState() == QtCore.Qt.Checked)

            client = {"host": host, "port": port, "enabled": enabled, "color-mode": color_mode,
                      "protocol": proto, "ignore-dimming": ignore_dimming}
            if client not in clients:
                clients.append(client)
        self.app.settings['networking']['clients'] = clients

    def accept_strands(self):
        strands = []
        for i in range(self.tbl_strands_list.rowCount()):
            idx = int(self.tbl_strands_list.item(i, 0).text())
            color_mode = self.tbl_strands_list.cellWidget(i, 1).currentText()
            enabled = (self.tbl_strands_list.cellWidget(i, 2).checkState() == QtCore.Qt.Checked)
            strand = {"id": idx, "enabled": enabled, "color-mode": color_mode}
            strands.append(strand)
        self.app.scene.set_strand_settings(strands)

    def save_settings(self):
        self.app.settings.save()
        self.app.scene.save()

    def populate_networking_clients_table(self):
        clients = self.app.settings['networking']['clients']
        self.tbl_networking_clients.setRowCount(len(clients))
        for i, client in enumerate(clients):
            item_host = QtWidgets.QTableWidgetItem(client["host"])
            item_port = QtWidgets.QTableWidgetItem(str(client["port"]))
            item_enabled = QtWidgets.QCheckBox()
            item_ignore_dimming = QtWidgets.QCheckBox()

            item_color_mode = QtWidgets.QComboBox()
            for mode in color_modes.modes:
                item_color_mode.addItem(mode)

            item_color_mode.setCurrentIndex(color_modes.modes.index(client["color-mode"]))

            if client["enabled"]:
                item_enabled.setCheckState(QtCore.Qt.Checked)

            if client.get("ignore-dimming", False):
                item_ignore_dimming.setCheckState(QtCore.Qt.Checked)

            item_protocol = QtWidgets.QComboBox()
            for proto in PROTOCOLS:
                item_protocol.addItem(proto)

            item_protocol.setCurrentIndex(PROTOCOLS.index(client["protocol"]))

            self.tbl_networking_clients.setItem(i, 0, item_host)
            self.tbl_networking_clients.setItem(i, 1, item_port)
            self.tbl_networking_clients.setCellWidget(i, 2, item_enabled)
            self.tbl_networking_clients.setCellWidget(i, 3, item_color_mode)
            self.tbl_networking_clients.setCellWidget(i, 4, item_protocol)
            self.tbl_networking_clients.setCellWidget(i, 5, item_ignore_dimming)
        self.tbl_networking_clients.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

    def add_networking_client_row(self):
        row = self.tbl_networking_clients.rowCount()
        self.tbl_networking_clients.insertRow(row)
        self.tbl_networking_clients.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self.tbl_networking_clients.setItem(row, 1, QtWidgets.QTableWidgetItem("3020"))
        self.tbl_networking_clients.setCellWidget(row, 2, QtWidgets.QCheckBox())
        item_color_mode = QtWidgets.QComboBox()
        for mode in color_modes.modes:
            item_color_mode.addItem(mode)

        item_protocol = QtWidgets.QComboBox()
        for proto in PROTOCOLS:
            item_protocol.addItem(proto)
        self.tbl_networking_clients.setCellWidget(row, 3, item_color_mode)
        self.tbl_networking_clients.setCellWidget(row, 4, item_protocol)

    def del_networking_client_row(self):
        self.tbl_networking_clients.removeRow(self.tbl_networking_clients.currentRow())

    def populate_strand_settings_table(self):
        strands = self.app.scene.get_strand_settings()
        self.tbl_strands_list.setRowCount(len(strands))
        self.tbl_strands_list.verticalHeader().setVisible(False)
        for i, strand in enumerate(strands):
            idx = QtWidgets.QTableWidgetItem(str(strand["id"]))
            idx.setFlags(QtCore.Qt.ItemFlags(idx.flags() & ~QtCore.Qt.ItemIsEnabled))

            enabled = QtWidgets.QCheckBox()
            if strand["enabled"]:
                enabled.setCheckState(QtCore.Qt.Checked)

            color_mode = QtWidgets.QComboBox()
            for mode in color_modes.strand_modes:
                color_mode.addItem(mode)

            color_mode.setCurrentIndex(color_modes.strand_modes.index(strand["color-mode"]))

            w_enabled = QtWidgets.QWidget()
            cb_layout = QtWidgets.QHBoxLayout()
            cb_layout.addWidget(enabled)
            cb_layout.setAlignment(QtCore.Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            w_enabled.setLayout(cb_layout)

            self.tbl_strands_list.setItem(i, 0, idx)
            self.tbl_strands_list.setCellWidget(i, 1, color_mode)
            # TODO: Use w_enabled rather than enabled (need to change the accept method)
            self.tbl_strands_list.setCellWidget(i, 2, enabled)

    def populate_mixer_settings(self):
        self.edit_onset_holdoff.setValue(self.app.settings.get("mixer")["onset-holdoff"])
        self.edit_tick_rate.setValue(self.app.settings.get("mixer")["tick-rate"])

    def validate_mixer(self):
        onset_holdoff = self.edit_onset_holdoff.value()
        tick_rate = self.edit_tick_rate.value()

        if onset_holdoff < 0.001 or onset_holdoff > 10.0:
            return False

        if tick_rate < 1 or tick_rate > 999999:
            return False

        return True

    def accept_mixer(self):
        onset_holdoff = self.edit_onset_holdoff.value()
        tick_rate = self.edit_tick_rate.value()

        self.app.settings.get("mixer")["onset-holdoff"] = onset_holdoff
        self.app.settings.get("mixer")["tick-rate"] = tick_rate

        QtCore.QMetaObject.invokeMethod(self.app.mixer, "restart")
